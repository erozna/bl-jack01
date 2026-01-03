import streamlit as st
import random
import time

# --- 1. 로직 함수 ---
def get_score(hand):
    if not hand: return 0
    score = 0
    aces = 0
    for card in hand:
        val = card[:-1]
        if val == 'A': aces += 1; score += 11
        elif val in ['J', 'Q', 'K', '10']: score += 10
        else: score += int(val)
    while score > 21 and aces > 0: score -= 10; aces -= 1
    return score

def get_basic_strategy(p_hand, d_upcard):
    p_score = get_score(p_hand)
    d_val_raw = d_upcard[:-1]
    d_val = 11 if d_val_raw == 'A' else (10 if d_val_raw in ['J', 'Q', 'K', '10'] else int(d_val_raw))
    
    # Pair Splitting (간소화)
    if len(p_hand) == 2 and p_hand[0][:-1] == p_hand[1][:-1]:
        if p_hand[0][:-1] in ['A', '8']: return "Split (P)"
    
    if p_score >= 17: return "Stand (S)"
    if 13 <= p_score <= 16: return "Stand (S)" if d_val <= 6 else "Hit (H)"
    if p_score == 11: return "Double (D)"
    return "Hit (H)"

# --- 2. 카드 그래픽 (CSS) ---
def card_html(card_str):
    if card_str == "?":
        return f"""<div style="display:inline-block; width:60px; height:85px; background:linear-gradient(135deg, #1a1a1a 25%, #444 100%); 
        color:white; border-radius:8px; margin:3px; text-align:center; line-height:85px; font-weight:bold; border:2px solid #555; box-shadow: 2px 2px 5px rgba(0,0,0,0.5);">?</div>"""
    suit = card_str[-1]
    val = card_str[:-1]
    color = "#ff4b4b" if suit in ['♥', '♦'] else "#31333F"
    return f"""
    <div style="display:inline-block; width:60px; height:85px; background:white; color:{color}; 
    border-radius:8px; margin:3px; padding:5px; position:relative; border:1px solid #ccc; 
    box-shadow: 3px 3px 8px rgba(0,0,0,0.2); font-family: 'Arial';">
        <div style="position:absolute; top:2px; left:5px; font-size:14px; font-weight:bold;">{val}</div>
        <div style="text-align:center; line-height:85px; font-size:20px;">{suit}</div>
    </div>
    """

# --- 3. 세션 상태 초기화 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'deck': [], 'rc': 0, 'hand_count': 0,
        'p_hands': [], 'd_hand': [], 'current_hand_idx': 0,
        'game_status': 'betting', 'msg': "배팅 후 DEAL을 누르세요."
    })

def reset_deck():
    suits = ['♠', '♥', '♦', '♣']
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
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
st.set_page_config(page_title="Split Enabled Blackjack", layout="wide")
st.title("🃏 블랙잭 프로 (스플릿 기능 포함)")

with st.sidebar:
    st.header("📊 통계")
    st.metric("현재 자산", f"{st.session_state.balance:,}원")
    st.write(f"🎮 게임: {st.session_state.hand_count}회 | 🎴 남은 카드: {len(st.session_state.deck)}장")
    if st.button("🔄 덱만 새로 섞기"): reset_deck(); st.rerun()
    auto_mode = st.checkbox("🤖 자동 플레이 (베이직 전략)")

if not st.session_state.deck: reset_deck()

col1, col2 = st.columns([2, 1])

with col1:
    # 딜러 영역
    st.subheader("Dealer Hand")
    d_display = "".join([card_html(c) if i == 0 or st.session_state.game_status == 'result' else card_html("?") 
                         for i, c in enumerate(st.session_state.d_hand)])
    st.markdown(d_display, unsafe_allow_html=True)
    st.divider()

    # 플레이어 영역 (멀티 핸드 대응)
    for idx, hand in enumerate(st.session_state.p_hands):
        is_active = (idx == st.session_state.current_hand_idx and st.session_state.game_status == 'playing')
        bg = "#333" if is_active else "transparent"
        st.markdown(f"<div style='background:{bg}; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
        st.subheader(f"Hand {idx+1} (Score: {get_score(hand)}) {'👈 현재 플레이 중' if is_active else ''}")
        st.markdown("".join([card_html(c) for c in hand]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.subheader("Control")
    st.info(st.session_state.msg)
    
    if st.session_state.game_status == 'betting':
        st.session_state.bet = st.slider("배팅액", 10000, 300000, 10000, step=10000)
        if st.button("DEAL", use_container_width=True):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.p_hands = [[draw_card(), draw_card()]]
                st.session_state.d_hand = [draw_card(), draw_card()]
                st.session_state.current_hand_idx = 0
                st.session_state.game_status = 'playing'
                st.session_state.hand_count += 1
                st.session_state.msg = "플레이 핸드를 선택하세요."
                st.rerun()

    elif st.session_state.game_status == 'playing':
        curr_hand = st.session_state.p_hands[st.session_state.current_hand_idx]
        st.write(f"현재 가이드: **{get_basic_strategy(curr_hand, st.session_state.d_hand[0])}**")
        
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("Hit"):
            curr_hand.append(draw_card())
            if get_score(curr_hand) >= 21:
                if st.session_state.current_hand_idx < len(st.session_state.p_hands) - 1:
                    st.session_state.current_hand_idx += 1
                else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        
        if c2.button("Stand"):
            if st.session_state.current_hand_idx < len(st.session_state.p_hands) - 1:
                st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
            
        if c3.button("Double", disabled=len(curr_hand) != 2):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                curr_hand.append(draw_card())
                if st.session_state.current_hand_idx < len(st.session_state.p_hands) - 1:
                    st.session_state.current_hand_idx += 1
                else: st.session_state.game_status = 'dealer_turn'
                st.rerun()

        # 스플릿 버튼 활성화 조건: 두 카드의 숫자가 같고, 핸드가 1개일 때
        can_split = len(curr_hand) == 2 and curr_hand[0][:-1] == curr_hand[1][:-1] and len(st.session_state.p_hands) == 1
        if c4.button("Split", disabled=not can_split):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                hand1 = [curr_hand[0], draw_card()]
                hand2 = [curr_hand[1], draw_card()]
                st.session_state.p_hands = [hand1, hand2]
                st.rerun()

# 결과 처리 로직
if st.session_state.game_status == 'dealer_turn':
    while get_score(st.session_state.d_hand) < 17:
        st.session_state.d_hand.append(draw_card())
    
    st.session_state.game_status = 'result'
    d_score = get_score(st.session_state.d_hand)
    final_msg = []
    
    for i, hand in enumerate(st.session_state.p_hands):
        p_score = get_score(hand)
        if p_score > 21: final_msg.append(f"H{i+1}: Bust 패배"); continue
        if d_score > 21 or p_score > d_score:
            st.session_state.balance += st.session_state.bet * 2
            final_msg.append(f"H{i+1}: 승리!")
        elif p_score < d_score: final_msg.append(f"H{i+1}: 패배")
        else:
            st.session_state.balance += st.session_state.bet
            final_msg.append(f"H{i+1}: 무승부")
    
    st.session_state.msg = " | ".join(final_msg)
    st.rerun()

if st.session_state.game_status == 'result':
    if st.button("NEXT GAME", use_container_width=True):
        st.session_state.game_status = 'betting'
        st.rerun()
