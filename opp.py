import streamlit as st
import random
import time
import pandas as pd

# --- 1. 로직 엔진 ---
def get_score(hand):
    if not hand: return 0
    score, aces = 0, 0
    for card in hand:
        val = card[:-1]
        if val == 'A': aces += 1; score += 11
        elif val in ['J', 'Q', 'K', '10']: score += 10
        else: score += int(val)
    while score > 21 and aces > 0: score -= 10; aces -= 1
    return score

def is_blackjack(hand):
    return len(hand) == 2 and get_score(hand) == 21

def get_basic_strategy(p_hand, d_upcard):
    if is_blackjack(p_hand): return "Blackjack!"
    p_score = get_score(p_hand)
    d_val_raw = d_upcard[:-1]
    d_val = 11 if d_val_raw == 'A' else (10 if d_val_raw in ['J', 'Q', 'K', '10'] else int(d_val_raw))
    
    if len(p_hand) == 2 and p_hand[0][:-1] == p_hand[1][:-1]:
        p_v = p_hand[0][:-1]
        if p_v in ['A', '8']: return "Split (P)"
        if p_v in ['2', '3', '7'] and d_val <= 7: return "Split (P)"
    
    if p_score >= 17: return "Stand (S)"
    if 13 <= p_score <= 16: return "Stand (S)" if d_val <= 6 else "Hit (H)"
    if p_score == 11: return "Double (D)"
    return "Hit (H)"

# --- 2. 카드 그래픽 (CSS) ---
def card_html(card_str):
    if card_str == "?":
        return f"""<div style="display:inline-block; width:55px; height:80px; background:linear-gradient(135deg, #1a1a1a 25%, #444 100%); 
        color:white; border-radius:8px; margin:2px; text-align:center; line-height:80px; font-weight:bold; border:2px solid #555;">?</div>"""
    suit, val = card_str[-1], card_str[:-1]
    color = "#ff4b4b" if suit in ['♥', '♦'] else "#31333F"
    return f"""
    <div style="display:inline-block; width:55px; height:80px; background:white; color:{color}; 
    border-radius:8px; margin:2px; padding:3px; position:relative; border:1px solid #ccc; 
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1); font-family: 'Arial';">
        <div style="position:absolute; top:2px; left:4px; font-size:12px; font-weight:bold; line-height:1;">{val}<br>{suit}</div>
        <div style="text-align:center; line-height:80px; font-size:18px;">{suit}</div>
    </div>
    """

# --- 3. 세션 상태 관리 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'ins_bet': 0, 'deck': [], 'rc': 0, 
        'hand_count': 0, 'wins': 0, 'losses': 0, 'draws': 0,
        'p_hands': [], 'd_hand': [], 'current_hand_idx': 0, 'history': [],
        'game_status': 'betting', 'msg': "Ready to Play", 'auto_mode': False
    })

def reset_deck():
    suits, values = ['♠', '♥', '♦', '♣'], ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    st.session_state.deck = [v + s for _ in range(8) for s in suits for v in values]
    random.shuffle(st.session_state.deck)
    st.session_state.rc = 0

def draw_card():
    if len(st.session_state.deck) < 20: reset_deck()
    card = st.session_state.deck.pop()
    v = card[:-1]
    if v in ['10', 'J', 'Q', 'K', 'A']: st.session_state.rc -= 1
    elif v in ['2', '3', '4', '5', '6']: st.session_state.rc += 1
    return card

# --- 4. 메인 UI ---
st.set_page_config(page_title="BK-Blackjack Pro", layout="wide")
st.title("🃏 BK-블랙잭")

# 전적 상단 표시
total_games = st.session_state.hand_count
win_rate = (st.session_state.wins / total_games * 100) if total_games > 0 else 0
st.markdown(f"""
### 📊 전적: {total_games}전 {st.session_state.wins}승 {st.session_state.draws}무 {st.session_state.losses}패 | 승률: {win_rate:.1f}%
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("💰 자산")
    st.metric("현재 잔액", f"{st.session_state.balance:,}원")
    
    if st.session_state.history:
        st.write("🕒 최근 기록")
        st.dataframe(pd.DataFrame(st.session_state.history).tail(8), hide_index=True)

    st.divider()
    if st.button("🔄 덱 새로 섞기"): reset_deck(); st.rerun()
    if st.button("💸 모든 데이터 초기화"): 
        st.session_state.balance = 2000000
        st.session_state.history = []
        st.session_state.hand_count = 0
        st.session_state.wins = 0
        st.session_state.losses = 0
        st.session_state.draws = 0
        reset_deck()
        st.rerun()
    st.divider()
    rem_decks = max(0.5, len(st.session_state.deck) / 52)
    st.metric("True Count", f"{st.session_state.rc / rem_decks:.2f}")
    st.session_state.auto_mode = st.checkbox("🤖 베이직 전략 자동 플레이")

col1, col2 = st.columns([2, 1])

with col1:
    d_score = get_score(st.session_state.d_hand) if st.session_state.game_status in ['dealer_turn', 'result'] else "?"
    st.subheader(f"Dealer Hand (Score: {d_score})")
    d_display = "".join([card_html(c) if i == 0 or st.session_state.game_status in ['dealer_turn', 'result'] else card_html("?") 
                         for i, c in enumerate(st.session_state.d_hand)])
    st.markdown(d_display, unsafe_allow_html=True)
    st.divider()

    for idx, hand in enumerate(st.session_state.p_hands):
        is_active = (idx == st.session_state.current_hand_idx and st.session_state.game_status == 'playing')
        st.markdown(f"<div style='border: {'2px solid yellow' if is_active else 'none'}; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
        st.subheader(f"Hand {idx+1} (Score: {get_score(hand)})")
        st.markdown("".join([card_html(c) for c in hand]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.subheader("Control Panel")
    st.info(st.session_state.msg)
    
    if st.session_state.game_status == 'betting':
        st.session_state.bet = st.slider("배팅액", 10000, 300000, 10000, step=5000)
        if st.button("DEAL START", use_container_width=True) or (st.session_state.auto_mode):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.p_hands = [[draw_card(), draw_card()]]
                st.session_state.d_hand = [draw_card(), draw_card()]
                st.session_state.ins_bet = 0
                st.session_state.current_hand_idx = 0
                st.session_state.hand_count += 1
                
                if is_blackjack(st.session_state.p_hands[0]) and st.session_state.d_hand[0][:-1] != 'A':
                    st.session_state.game_status = 'dealer_turn'
                    st.session_state.msg = "Blackjack! 1.5배 보너스"
                else:
                    st.session_state.game_status = 'playing'
                    st.session_state.msg = "진행 중..."
                st.rerun()

    elif st.session_state.game_status == 'playing':
        curr_h = st.session_state.p_hands[st.session_state.current_hand_idx]
        action = get_basic_strategy(curr_h, st.session_state.d_hand[0])
        st.write(f"가이드: **{action}**")
        
        if st.session_state.d_hand[0][:-1] == 'A' and st.session_state.ins_bet == 0:
            if st.button(f"Insurance ({st.session_state.bet//2:,}원)"):
                st.session_state.balance -= (st.session_state.bet // 2)
                st.session_state.ins_bet = st.session_state.bet // 2
                st.rerun()

        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Hit") or (st.session_state.auto_mode and "Hit" in action):
            curr_h.append(draw_card()); st.rerun()
        if c2.button("Stand") or (st.session_state.auto_mode and "Stand" in action):
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if c3.button("Double") or (st.session_state.auto_mode and "Double" in action):
            st.session_state.balance -= st.session_state.bet
            st.session_state.bet *= 2
            curr_h.append(draw_card())
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        can_split = len(curr_h) == 2 and curr_h[0][:-1] == curr_h[1][:-1] and len(st.session_state.p_hands) == 1
        if c4.button("Split", disabled=not can_split) or (st.session_state.auto_mode and "Split" in action and can_split):
            st.session_state.balance -= st.session_state.bet
            st.session_state.p_hands = [[curr_h[0], draw_card()], [curr_h[1], draw_card()]]
            st.rerun()

if st.session_state.game_status == 'dealer_turn':
    while get_score(st.session_state.d_hand) < 17:
        st.session_state.d_hand.append(draw_card())
    st.session_state.game_status = 'result'
    st.rerun()

if st.session_state.game_status == 'result':
    d_s, d_bj = get_score(st.session_state.d_hand), is_blackjack(st.session_state.d_hand)
    if d_bj and st.session_state.ins_bet > 0:
        st.session_state.balance += st.session_state.ins_bet * 3
    
    results, total_payout = [], 0
    final_win_flag, final_draw_flag = False, False # 전적 기록용
    
    for h in st.session_state.p_hands:
        p_s, p_bj = get_score(h), is_blackjack(h)
        if p_bj:
            if d_bj: payout = st.session_state.bet; res = "BJ Push"; final_draw_flag = True
            else: payout = int(st.session_state.bet * 2.5); res = "BJ Win"; final_win_flag = True
        elif p_s > 21: payout = 0; res = "Bust"
        elif d_s > 21 or p_s > d_s: payout = st.session_state.bet * 2; res = "Win"; final_win_flag = True
        elif p_s < d_s: payout = 0; res = "Loss"
        else: payout = st.session_state.bet; res = "Push"; final_draw_flag = True
        total_payout += payout
        results.append(res)
    
    # 전적 업데이트 (한 판에 여러 핸드가 있어도 1회 게임으로 카운트)
    if final_win_flag: st.session_state.wins += 1
    elif final_draw_flag: st.session_state.draws += 1
    else: st.session_state.losses += 1

    st.session_state.balance += total_payout
    st.session_state.history.append({"No": total_games, "Result": ", ".join(results), "Balance": f"{st.session_state.balance:,}"})
    st.session_state.msg = " | ".join(results)
    
    if st.button("NEXT GAME", use_container_width=True) or st.session_state.auto_mode:
        if st.session_state.auto_mode: time.sleep(1.0)
        st.session_state.game_status = 'betting'
        st.rerun()
