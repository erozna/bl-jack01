import streamlit as st
import random
import time

# --- 1. 베이직 전략 및 점수 로직 ---
def get_score(hand):
    score = 0
    aces = 0
    for card in hand:
        val = card[:-1] # 카드에서 모양 제외한 값
        if val == 'A': aces += 1; score += 11
        elif val in ['J', 'Q', 'K', '10']: score += 10
        else: score += int(val)
    while score > 21 and aces > 0: score -= 10; aces -= 1
    return score

def get_basic_strategy(p_hand, d_upcard):
    p_score = get_score(p_hand)
    d_val_raw = d_upcard[:-1]
    d_val = 11 if d_val_raw == 'A' else (10 if d_val_raw in ['J', 'Q', 'K', '10'] else int(d_val_raw))
    
    if p_score >= 17: return "Stand (S)"
    if 13 <= p_score <= 16: return "Stand (S)" if d_val <= 6 else "Hit (H)"
    if p_score == 12: return "Stand (S)" if d_val in [4, 5, 6] else "Hit (H)"
    if p_score == 11: return "Double (D)"
    if p_score == 10: return "Double (D)" if d_val <= 9 else "Hit (H)"
    if p_score == 9: return "Double (D)" if d_val in [3, 4, 5, 6] else "Hit (H)"
    return "Hit (H)"

# --- 2. 카드 그래픽 디자인 (CSS 강화) ---
def card_html(card_str):
    if card_str == "?":
        return f"""<div style="display:inline-block; width:65px; height:95px; background:linear-gradient(135deg, #1a1a1a 25%, #444 100%); 
        color:white; border-radius:8px; margin:5px; text-align:center; line-height:95px; font-weight:bold; border:2px solid #555; box-shadow: 2px 2px 5px rgba(0,0,0,0.5);">?</div>"""
    
    suit = card_str[-1]
    val = card_str[:-1]
    color = "#ff4b4b" if suit in ['♥', '♦'] else "#31333F"
    
    return f"""
    <div style="display:inline-block; width:65px; height:95px; background:white; color:{color}; 
    border-radius:8px; margin:5px; padding:5px; position:relative; border:1px solid #ccc; 
    box-shadow: 3px 3px 8px rgba(0,0,0,0.2); font-family: 'Arial';">
        <div style="position:absolute; top:5px; left:5px; font-size:16px; font-weight:bold; line-height:1;">{val}<br><span style="font-size:12px;">{suit}</span></div>
        <div style="text-align:center; line-height:95px; font-size:24px;">{suit}</div>
        <div style="position:absolute; bottom:5px; right:5px; font-size:16px; font-weight:bold; transform: rotate(180deg); line-height:1;">{val}<br><span style="font-size:12px;">{suit}</span></div>
    </div>
    """

# --- 3. 세션 상태 관리 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'deck': [], 'rc': 0, 'hand_count': 0,
        'p_hand': [], 'd_hand': [], 'game_status': 'betting', 'msg': "배팅 후 게임을 시작하세요."
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
    val = card[:-1]
    if val in ['10', 'J', 'Q', 'K', 'A']: st.session_state.rc -= 1
    elif val in ['2', '3', '4', '5', '6']: st.session_state.rc += 1
    return card

# --- 4. 메인 UI ---
st.set_page_config(page_title="Advanced Blackjack", layout="wide")
st.markdown("<style>.metric-box { background: #262730; padding: 15px; border-radius: 10px; }</style>", unsafe_allow_html=True)

st.title("🃏 프로페셔널 블랙잭 시뮬레이터")

# 사이드바: 통계 및 덱 제어
with st.sidebar:
    st.header("📊 통계 및 설정")
    st.metric("현재 자산", f"{st.session_state.balance:,}원")
    st.write(f"🎮 게임 횟수: **{st.session_state.hand_count}회**")
    st.write(f"🎴 남은 카드: **{len(st.session_state.deck)}장**")
    
    st.divider()
    if st.button("🔄 카드만 새로 섞기 (자산 유지)", use_container_width=True):
        reset_deck()
        st.success("덱이 초기화되었습니다.")
    
    if st.button("💸 자산 초기화 (200만)", use_container_width=True):
        st.session_state.balance = 2000000
        st.session_state.hand_count = 0
        reset_deck()
        st.rerun()

    st.divider()
    rem_decks = max(1, len(st.session_state.deck) / 52)
    st.metric("True Count", f"{st.session_state.rc / rem_decks:.2f}")
    auto_mode = st.checkbox("🤖 베이직 전략 자동 플레이")

# 메인 게임 레이아웃
if not st.session_state.deck: reset_deck()

col1, col2 = st.columns([2, 1])

with col1:
    # 딜러 영역
    d_score = get_score(st.session_state.d_hand) if st.session_state.game_status != 'playing' else "?"
    st.subheader(f"Dealer Hand (Score: {d_score})")
    d_display = "".join([card_html(c) if i == 0 or st.session_state.game_status != 'playing' else card_html("?") 
                         for i, c in enumerate(st.session_state.d_hand)])
    st.markdown(d_display, unsafe_allow_html=True)

    st.divider()

    # 플레이어 영역
    p_score = get_score(st.session_state.p_hand)
    st.subheader(f"Player Hand (Score: {p_score})")
    p_display = "".join([card_html(c) for c in st.session_state.p_hand])
    st.markdown(p_display, unsafe_allow_html=True)
    
    if st.session_state.game_status == 'playing':
        rec = get_basic_strategy(st.session_state.p_hand, st.session_state.d_hand[0])
        st.info(f"💡 가이드: {rec}")

with col2:
    st.subheader("Control")
    st.write(f"📢 {st.session_state.msg}")
    
    if st.session_state.game_status == 'betting':
        st.session_state.bet = st.slider("배팅액 설정", 10000, 300000, 10000, step=10000)
        if st.button("DEAL", use_container_width=True):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.p_hand = [draw_card(), draw_card()]
                st.session_state.d_hand = [draw_card(), draw_card()]
                st.session_state.game_status = 'playing'
                st.session_state.hand_count += 1
                st.rerun()
            else: st.error("잔액 부족!")

    elif st.session_state.game_status == 'playing':
        btn_cols = st.columns(3)
        if btn_cols[0].button("Hit"):
            st.session_state.p_hand.append(draw_card())
            if get_score(st.session_state.p_hand) > 21:
                st.session_state.game_status = 'betting'
                st.session_state.msg = "Bust! 딜러 승리"
            st.rerun()
        if btn_cols[1].button("Stand"):
            st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if btn_cols[2].button("Double"):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.bet *= 2
                st.session_state.p_hand.append(draw_card())
                st.session_state.game_status = 'dealer_turn'
                st.rerun()

# 딜러 AI 및 결과 처리
if st.session_state.game_status == 'dealer_turn':
    while get_score(st.session_state.d_hand) < 17:
        st.session_state.d_hand.append(draw_card())
    
    ps, ds = get_score(st.session_state.p_hand), get_score(st.session_state.d_hand)
    if ds > 21 or ps > ds:
        st.session_state.balance += st.session_state.bet * 2
        st.session_state.msg = f"승리! {st.session_state.bet*2:,}원 획득"
    elif ps < ds: st.session_state.msg = "딜러 승리"
    else:
        st.session_state.balance += st.session_state.bet
        st.session_state.msg = "무승부 (Push)"
    
    st.session_state.game_status = 'betting'
    st.rerun()

# 자동 플레이 (베이직 전략 기반)
if auto_mode and st.session_state.game_status == 'playing':
    time.sleep(0.8)
    action = get_basic_strategy(st.session_state.p_hand, st.session_state.d_hand[0])
    if "Hit" in action:
        st.session_state.p_hand.append(draw_card())
        if get_score(st.session_state.p_hand) > 21: st.session_state.game_status = 'betting'
    elif "Double" in action:
        st.session_state.balance -= st.session_state.bet
        st.session_state.bet *= 2
        st.session_state.p_hand.append(draw_card())
        st.session_state.game_status = 'dealer_turn'
    else: st.session_state.game_status = 'dealer_turn'
    st.rerun()
