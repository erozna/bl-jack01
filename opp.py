import streamlit as st
import random
import time

# --- 1. 베이직 전략 엔진 (Hard Totals, Soft Totals, Pairs) ---
def get_basic_strategy(p_hand, d_upcard, is_split=False):
    p_score = get_score(p_hand)
    d_val = 11 if d_upcard == 'A' else (10 if d_upcard in ['J', 'Q', 'K'] else int(d_upcard))
    is_soft = 'A' in p_hand and get_score(p_hand) <= 21 and len(p_hand) == 2 # 단순화된 소프트 체크
    
    # 1. Pair Splitting
    if len(p_hand) == 2 and p_hand[0] == p_hand[1]:
        p_val = 11 if p_hand[0] == 'A' else (10 if p_hand[0] in ['J', 'Q', 'K'] else int(p_hand[0]))
        if p_val in [8, 11]: return "Split (P)"
        if p_val == 2 and d_val <= 7: return "Split (P)"
        if p_val == 3 and d_val <= 7: return "Split (P)"
        if p_val == 4 and d_val in [5, 6]: return "Split (P)"
        if p_val == 6 and d_val <= 6: return "Split (P)"
        if p_val == 7 and d_val <= 7: return "Split (P)"
        if p_val == 9 and d_val not in [7, 10, 11]: return "Split (P)"

    # 2. Soft Totals (A + X)
    if is_soft:
        non_ace = p_score - 11
        if non_ace >= 8: return "Stand (S)"
        if non_ace == 7: return "Stand (S)" if d_val <= 8 else "Hit (H)"
        return "Hit (H)"

    # 3. Hard Totals
    if p_score >= 17: return "Stand (S)"
    if p_score >= 13 and d_val <= 6: return "Stand (S)"
    if p_score == 12 and d_val in [4, 5, 6]: return "Stand (S)"
    if p_score == 11: return "Double (D)"
    if p_score == 10 and d_val <= 9: return "Double (D)"
    if p_score == 9 and d_val in [3, 4, 5, 6]: return "Double (D)"
    
    return "Hit (H)"

def get_score(hand):
    score = 0
    aces = 0
    for card in hand:
        if card == 'A': aces += 1; score += 11
        elif card in ['J', 'Q', 'K']: score += 10
        else: score += int(card)
    while score > 21 and aces > 0: score -= 10; aces -= 1
    return score

# --- 2. 카드/UI 컴포넌트 ---
def card_html(card):
    color = "#ff4b4b" if card in ['♥', '♦'] else "#31333F"
    return f"""<div style="display:inline-block; width:50px; height:80px; background:white; color:black; 
    border-radius:5px; margin:5px; text-align:center; line-height:80px; font-weight:bold; border:2px solid #ddd;">{card}</div>"""

# --- 3. 세션 상태 관리 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'deck': [], 'rc': 0,
        'p_hand': [], 'd_hand': [], 'game_status': 'betting', 'msg': "배팅 금액을 정하고 게임을 시작하세요.",
        'auto_mode': False
    })

def reset_deck():
    suits = ['♠', '♥', '♦', '♣'] * 8
    values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    st.session_state.deck = [v for v in values for _ in suits]
    random.shuffle(st.session_state.deck)
    st.session_state.rc = 0

def draw_card():
    if len(st.session_state.deck) < 20: reset_deck()
    card = st.session_state.deck.pop()
    # 카운팅 업데이트
    if card in ['10', 'J', 'Q', 'K', 'A']: st.session_state.rc -= 1
    elif card in ['2', '3', '4', '5', '6']: st.session_state.rc += 1
    return card

# --- 4. 메인 화면 구성 ---
st.set_page_config(page_title="Pro Blackjack Simulator", layout="wide")
st.title("🃏 전문가용 블랙잭 시뮬레이터")

# 사이드바: 통계 및 설정
with st.sidebar:
    st.header("💰 자산 관리")
    st.metric("현재 잔액", f"{st.session_state.balance:,}원")
    st.session_state.bet = st.number_input("배팅 (1만~30만)", 10000, 300000, step=10000)
    if st.button("자산 초기화 (200만)"): 
        st.session_state.balance = 2000000
        st.rerun()
    
    st.divider()
    st.header("📊 카드 카운팅")
    rem_decks = max(1, len(st.session_state.deck) / 52)
    st.write(f"Running Count: **{st.session_state.rc}**")
    st.write(f"True Count: **{st.session_state.rc / rem_decks:.2f}**")
    st.session_state.auto_mode = st.checkbox("🤖 자동 플레이 모드 (Basic Strategy)")

# 게임 화면
col1, col2 = st.columns([2, 1])

with col1:
    # 딜러 영역
    st.subheader("Dealer Hand")
    d_html = ""
    if st.session_state.game_status == 'playing':
        d_html = card_html(st.session_state.d_hand[0]) + card_html("?")
    else:
        d_html = "".join([card_html(c) for c in st.session_state.d_hand])
    st.markdown(d_html, unsafe_allow_html=True)

    st.divider()

    # 플레이어 영역
    st.subheader("Player Hand")
    p_html = "".join([card_html(c) for c in st.session_state.p_hand])
    st.markdown(p_html, unsafe_allow_html=True)
    
    if st.session_state.p_hand:
        strategy = get_basic_strategy(st.session_state.p_hand, st.session_state.d_hand[0])
        st.info(f"💡 베이직 전략 추천: **{strategy}**")

with col2:
    st.subheader("Game Control")
    st.write(st.session_state.msg)
    
    if st.session_state.game_status == 'betting':
        if st.button("DEAL START", use_container_width=True):
            if st.session_state.balance < st.session_state.bet:
                st.error("잔액이 부족합니다!")
            else:
                st.session_state.balance -= st.session_state.bet
                st.session_state.p_hand = [draw_card(), draw_card()]
                st.session_state.d_hand = [draw_card(), draw_card()]
                st.session_state.game_status = 'playing'
                st.session_state.msg = "진행 중..."
                st.rerun()

    elif st.session_state.game_status == 'playing':
        c1, c2, c3 = st.columns(3)
        if c1.button("Hit"):
            st.session_state.p_hand.append(draw_card())
            if get_score(st.session_state.p_hand) > 21:
                st.session_state.game_status = 'betting'
                st.session_state.msg = "Bust! 딜러 승리"
            st.rerun()
            
        if c2.button("Stand"):
            st.session_state.game_status = 'dealer_turn'
            st.rerun()
            
        if c3.button("Double"):
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.balance -= st.session_state.bet
                st.session_state.bet *= 2
                st.session_state.p_hand.append(draw_card())
                st.session_state.game_status = 'dealer_turn'
                st.rerun()
            else: st.warning("잔액 부족!")

# 딜러 턴 로직 (자동화 포함)
if st.session_state.game_status == 'dealer_turn':
    while get_score(st.session_state.d_hand) < 17:
        st.session_state.d_hand.append(draw_card())
    
    p_s = get_score(st.session_state.p_hand)
    d_s = get_score(st.session_state.d_hand)
    
    # 승패 계산
    bet = st.session_state.bet
    if d_s > 21 or p_s > d_s:
        st.session_state.msg = f"승리! {bet*2:,}원 획득"
        st.session_state.balance += bet * 2
    elif p_s < d_s:
        st.session_state.msg = "딜러 승리"
    else:
        st.session_state.msg = "무승부"
        st.session_state.balance += bet
        
    st.session_state.game_status = 'betting'
    # 더블다운 후 배팅 원복
    st.session_state.bet = 10000 
    st.rerun()

# --- 5. 자동 플레이 모드 (Experimental) ---
if st.session_state.auto_mode and st.session_state.game_status == 'playing':
    time.sleep(1) # 눈으로 따라갈 수 있게 지연
    action = get_basic_strategy(st.session_state.p_hand, st.session_state.d_hand[0])
    if "Hit" in action:
        st.session_state.p_hand.append(draw_card())
        if get_score(st.session_state.p_hand) > 21:
            st.session_state.game_status = 'betting'
        st.rerun()
    elif "Double" in action:
        # 더블다운 로직 실행 후 스탠드와 동일 처리
        st.session_state.balance -= st.session_state.bet
        st.session_state.bet *= 2
        st.session_state.p_hand.append(draw_card())
        st.session_state.game_status = 'dealer_turn'
        st.rerun()
    else: # Stand
        st.session_state.game_status = 'dealer_turn'
        st.rerun()