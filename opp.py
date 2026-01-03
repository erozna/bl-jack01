import streamlit as st
import random
import time

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
        return f"""<div style="display:inline-block; width:60px; height:85px; background:linear-gradient(135deg, #1a1a1a 25%, #444 100%); 
        color:white; border-radius:8px; margin:3px; text-align:center; line-height:85px; font-weight:bold; border:2px solid #555;">?</div>"""
    suit, val = card_str[-1], card_str[:-1]
    color = "#ff4b4b" if suit in ['♥', '♦'] else "#31333F"
    return f"""
    <div style="display:inline-block; width:60px; height:85px; background:white; color:{color}; 
    border-radius:8px; margin:3px; padding:5px; position:relative; border:1px solid #ccc; 
    box-shadow: 3px 3px 8px rgba(0,0,0,0.2); font-family: 'Arial';">
        <div style="position:absolute; top:2px; left:5px; font-size:14px; font-weight:bold; line-height:1.1;">{val}<br><span style="font-size:10px;">{suit}</span></div>
        <div style="text-align:center; line-height:85px; font-size:20px;">{suit}</div>
    </div>
    """

# --- 3. 세션 상태 관리 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'ins_bet': 0, 'deck': [], 'rc': 0, 'hand_count': 0,
        'p_hands': [], 'd_hand': [], 'current_hand_idx': 0,
        'game_status': 'betting', 'msg': "배팅 후 DEAL을 누르세요.", 'auto_mode': False
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

with st.sidebar:
    st.header("📊 통계 센터")
    st.metric("현재 자산", f"{st.session_state.balance:,}원")
    st.write(f"🎮 게임 횟수: **{st.session_state.hand_count}**")
    if st.button("🔄 덱 새로 섞기"): reset_deck(); st.rerun()
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
        st.session_state.bet = st.slider("배팅액", 10000, 300000, 10000, step=10000)
        if st.button("DEAL START", use_container_width=True) or (st.session_state.auto_mode):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.p_hands = [[draw_card(), draw_card()]]
                st.session_state.d_hand = [draw_card(), draw_card()]
                st.session_state.ins_bet = 0
                st.session_state.current_hand_idx = 0
                st.session_state.hand_count += 1
                
                # 딜러가 A가 아니고 플레이어가 블랙잭이면 즉시 승리
                if is_blackjack(st.session_state.p_hands[0]) and st.session_state.d_hand[0][:-1] != 'A':
                    st.session_state.game_status = 'dealer_turn'
                    st.session_state.msg = "Blackjack! 1.5배 즉시 지급"
                else:
                    st.session_state.game_status = 'playing'
                    st.session_state.msg = "진행 중..."
                st.rerun()

    elif st.session_state.game_status == 'playing':
        curr_h = st.session_state.p_hands[st.session_state.current_hand_idx]
        action = get_basic_strategy(curr_h, st.session_state.d_hand[0])
        st.write(f"가이드: **{action}**")
        
        # 인슈어런스 로직
        if st.session_state.d_hand[0][:-1] == 'A' and st.session_state.ins_bet == 0:
            if st.button(f"Insurance ({st.session_state.bet//2:,}원)"):
                st.session_state.balance -= (st.session_state.bet // 2)
                st.session_state.ins_bet = st.session_state.bet // 2
                st.session_state.msg = "인슈어런스 적용됨. 게임을 계속하세요."
                st.rerun()

        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Hit") or (st.session_state.auto_mode and action == "Hit (H)"):
            curr_h.append(draw_card())
            if get_score(curr_h) >= 21:
                if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
                else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if c2.button("Stand") or (st.session_state.auto_mode and action == "Stand (S)"):
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if c3.button("Double") or (st.session_state.auto_mode and action == "Double (D)"):
            st.session_state.balance -= st.session_state.bet
            st.session_state.bet *= 2
            curr_h.append(draw_card())
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        can_split = len(curr_h) == 2 and curr_h[0][:-1] == curr_h[1][:-1] and len(st.session_state.p_hands) == 1
        if c4.button("Split", disabled=not can_split) or (st.session_state.auto_mode and action == "Split (P)" and can_split):
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
    
    # 인슈어런스 정산: 딜러 BJ이면 인슈어런스 배팅금의 3배(본전 회수+2배 수익) 지급
    if d_bj and st.session_state.ins_bet > 0:
        st.session_state.balance += st.session_state.ins_bet * 3
        st.toast("Insurance 성공!")

    res_msgs = []
    original_bet = st.session_state.bet # 더블다운 시 변한 배팅액 고려
    
    for h in st.session_state.p_hands:
        p_s, p_bj = get_score(h), is_blackjack(h)
        if p_bj:
            if d_bj: st.session_state.balance += original_bet; res_msgs.append("BJ Push")
            else: st.session_state.balance += int(original_bet * 2.5); res_msgs.append("BJ Win(1.5x)")
        elif p_s > 21: res_msgs.append("Bust")
        elif d_s > 21 or p_s > d_s:
            st.session_state.balance += original_bet * 2
            res_msgs.append("Win")
        elif p_s < d_s: res_msgs.append("Loss")
        else: st.session_state.balance += original_bet; res_msgs.append("Push")
    
    st.session_state.msg = " | ".join(res_msgs)
    if st.button("NEXT GAME", use_container_width=True) or st.session_state.auto_mode:
        time.sleep(1.5) if st.session_state.auto_mode else None
        st.session_state.game_status = 'betting'
        st.session_state.bet = 10000 # 배팅 초기화
        st.rerun()
