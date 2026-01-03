import streamlit as st
import random
import time
import pandas as pd

# --- 1. 로직 엔진 ---
def 점수_계산(카드_뭉치):
    if not 카드_뭉치: return 0
    점수, 에이스_개수 = 0, 0
    for 카드 in 카드_뭉치:
        값 = 카드[:-1]
        if 값 == 'A': 에이스_개수 += 1; 점수 += 11
        elif 값 in ['J', 'Q', 'K', '10']: 점수 += 10
        else: 점수 += int(값)
    while 점수 > 21 and 에이스_개수 > 0: 점수 -= 10; 에이스_개수 -= 1
    return 점수

def 블랙잭_확인(카드_뭉치):
    return len(카드_뭉치) == 2 and 점수_계산(카드_뭉치) == 21

def 전략_가이드(내_카드, 딜러_카드):
    if 블랙잭_확인(내_카드): return "블랙잭!"
    내_점수 = 점수_계산(내_카드)
    딜러_값 = 11 if 딜러_카드[:-1] == 'A' else (10 if 딜러_카드[:-1] in ['J', 'Q', 'K', '10'] else int(딜러_카드[:-1]))
    
    if len(내_카드) == 2:
        카드1_값 = 10 if 내_카드[0][:-1] in ['10', 'J', 'Q', 'K'] else (11 if 내_카드[0][:-1] == 'A' else int(내_카드[0][:-1]))
        카드2_값 = 10 if 내_카드[1][:-1] in ['10', 'J', 'Q', 'K'] else (11 if 내_카드[1][:-1] == 'A' else int(내_카드[1][:-1]))
        if 카드1_값 == 카드2_값:
            if 내_카드[0][:-1] in ['A', '8']: return "찢기 (P)"
            if 내_카드[0][:-1] in ['2', '3', '7'] and 딜러_값 <= 7: return "찢기 (P)"
    
    if 내_점수 >= 17: return "멈춤 (S)"
    if 13 <= 내_점수 <= 16: return "멈춤 (S)" if 딜러_값 <= 6 else "받기 (H)"
    if 내_점수 == 11: return "두배 (D)"
    if 내_점수 == 16 and 딜러_값 >= 9: return "포기 (R)"
    return "받기 (H)"

# --- 2. 카드 렌더링 ---
def 카드_렌더링(카드_문자열):
    if 카드_문자열 == "?":
        return f"""<div style="display:inline-block; width:55px; height:80px; background:linear-gradient(135deg, #1a1a1a 25%, #444 100%); color:white; border-radius:8px; margin:2px; text-align:center; line-height:80px; font-weight:bold; border:2px solid #555;">?</div>"""
    문양, 숫자 = 카드_문자열[-1], 카드_문자열[:-1]
    색상 = "#ff4b4b" if 문양 in ['♥', '♦'] else "#31333F"
    return f"""<div style="display:inline-block; width:55px; height:80px; background:white; color:{색상}; border-radius:8px; margin:2px; padding:3px; position:relative; border:1px solid #ccc; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); font-family: 'Arial';"><div style="position:absolute; top:2px; left:4px; font-size:12px; font-weight:bold; line-height:1;">{숫자}<br>{문양}</div><div style="text-align:center; line-height:80px; font-size:18px;">{문양}</div></div>"""

# --- 3. 세션 관리 ---
if 'balance' not in st.session_state:
    st.session_state.update({
        'balance': 2000000, 'bet': 10000, 'ins_bet': 0, 'deck': [], 'rc': 0, 'wins': 0, 'losses': 0, 'draws': 0,
        'p_hands': [], 'd_hand': [], 'current_hand_idx': 0, 'history': [], 'game_status': 'betting', 'msg': "배팅 후 게임을 시작하세요.", 
        'auto_mode': False, 'processed': False, 'aa_split': False
    })

def 덱_초기화():
    문양들, 숫자들 = ['♠', '♥', '♦', '♣'], ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    st.session_state.deck = [숫자 + 문양 for _ in range(8) for 문양 in 문양들 for 숫자 in 숫자들]
    random.shuffle(st.session_state.deck)
    st.session_state.rc = 0

def 카드_뽑기():
    if len(st.session_state.deck) < 20: 덱_초기화()
    카드 = st.session_state.deck.pop()
    v = 카드[:-1]
    if v in ['10', 'J', 'Q', 'K', 'A']: st.session_state.rc -= 1
    elif v in ['2', '3', '4', '5', '6']: st.session_state.rc += 1
    return 카드

# --- 4. 메인 화면 ---
st.set_page_config(page_title="BK-블랙잭 프로", layout="wide")
st.title("🃏 BK-블랙잭 (표준 카지노 규칙)")

# 상단 전적 표시
판수 = st.session_state.wins + st.session_state.draws + st.session_state.losses
승률 = (st.session_state.wins / 판수 * 100) if 판수 > 0 else 0
st.markdown(f"### 📊 전적: {판수}전 {st.session_state.wins}승 {st.session_state.draws}무 {st.session_state.losses}패 | 승률: {승률:.1f}%")

with st.sidebar:
    st.header("💰 자산 및 도구")
    st.metric("현재 잔액", f"{st.session_state.balance:,}원")
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history).tail(5), hide_index=True)
    if st.button("💸 전체 초기화"): 
        st.session_state.update({'balance': 2000000, 'history': [], 'wins': 0, 'losses': 0, 'draws': 0})
        덱_초기화(); st.rerun()
    st.divider()
    rem_decks = max(0.5, len(st.session_state.deck) / 52)
    st.metric("트루 카운트", f"{st.session_state.rc / rem_decks:.2f}")
    st.session_state.auto_mode = st.checkbox("🤖 자동 플레이 모드")

if not st.session_state.deck: 덱_초기화()

col1, col2 = st.columns([2, 1])

with col1:
    # 딜러 영역
    딜러_점수 = 점수_계산(st.session_state.d_hand) if st.session_state.game_status in ['dealer_turn', 'result'] else "?"
    st.subheader(f"딜러 (점수: {딜러_점수})")
    딜러_카드_출력 = "".join([카드_렌더링(c) if i == 0 or st.session_state.game_status in ['dealer_turn', 'result'] else 카드_렌더링("?") for i, c in enumerate(st.session_state.d_hand)])
    st.markdown(딜러_카드_출력, unsafe_allow_html=True)
    st.divider()

    # 플레이어 영역
    for idx, 핸디 in enumerate(st.session_state.p_hands):
        활성화 = (idx == st.session_state.current_hand_idx and st.session_state.game_status == 'playing')
        st.markdown(f"<div style='border: {'2px solid yellow' if 활성화 else 'none'}; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
        st.subheader(f"핸디 {idx+1} (점수: {점수_계산(핸디)})")
        st.markdown("".join([카드_렌더링(c) for c in 핸디]), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.subheader("조작판")
    st.info(st.session_state.msg)
    
    if st.session_state.game_status == 'betting':
        st.session_state.bet = st.slider("배팅액 설정", 10000, 300000, 10000, step=5000)
        if st.button("게임 시작", use_container_width=True) or st.session_state.auto_mode:
            if st.session_state.balance >= st.session_state.bet:
                st.session_state.update({'balance': st.session_state.balance - st.session_state.bet, 'p_hands': [[카드_뽑기(), 카드_뽑기()]], 'd_hand': [카드_뽑기(), 카드_뽑기()], 'ins_bet': 0, 'current_hand_idx': 0, 'processed': False, 'aa_split': False})
                if 블랙잭_확인(st.session_state.p_hands[0]) and st.session_state.d_hand[0][:-1] != 'A':
                    st.session_state.game_status = 'dealer_turn'
                else:
                    st.session_state.game_status = 'playing'
                    st.session_state.msg = "동작을 선택하세요."
                st.rerun()

    elif st.session_state.game_status == 'playing':
        현재_핸디 = st.session_state.p_hands[st.session_state.current_hand_idx]
        가이드 = 전략_가이드(현재_핸디, st.session_state.d_hand[0])
        st.write(f"추천 전략: **{가이드}**")
        
        c1, c2, c3, c4, c5 = st.columns(5)
        if c1.button("받기(H)") or (st.session_state.auto_mode and "받기" in 가이드):
            현재_핸디.append(카드_뽑기())
            if 점수_계산(현재_핸디) >= 21:
                if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
                else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if c2.button("멈춤(S)") or (st.session_state.auto_mode and "멈춤" in 가이드):
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        if c3.button("두배(D)") or (st.session_state.auto_mode and "두배" in 가이드):
            st.session_state.balance -= st.session_state.bet
            st.session_state.bet *= 2
            현재_핸디.append(카드_뽑기())
            if st.session_state.current_hand_idx < len(st.session_state.p_hands)-1: st.session_state.current_hand_idx += 1
            else: st.session_state.game_status = 'dealer_turn'
            st.rerun()
        
        찢기가능 = len(현재_핸디) == 2 and 점수_계산([현재_핸디[0]]) == 점수_계산([현재_핸디[1]]) and len(st.session_state.p_hands) == 1
        if c4.button("찢기(P)", disabled=not 찢기가능) or (st.session_state.auto_mode and "찢기" in 가이드 and 찢기가능):
            is_aa = (현재_핸디[0][:-1] == 'A')
            st.session_state.balance -= st.session_state.bet
            hand1, hand2 = [현재_핸디[0], 카드_뽑기()], [현재_핸디[1], 카드_뽑기()]
            st.session_state.p_hands = [hand1, hand2]
            if is_aa: # AA 찢기 특수 룰 적용
                st.session_state.msg = "AA 찢기: 각 1장씩만 받고 종료됩니다."
                st.session_state.game_status = 'dealer_turn'
            st.rerun()
        
        포기가능 = len(현재_핸디) == 2 and len(st.session_state.p_hands) == 1
        if c5.button("포기(R)", disabled=not 포기가능) or (st.session_state.auto_mode and "포기" in 가이드 and 포기가능):
            st.session_state.balance += st.session_state.bet // 2
            st.session_state.msg = "서렌더: 배팅액 절반 회수"
            st.session_state.losses += 1
            st.session_state.game_status = 'betting'
            st.rerun()

    elif st.session_state.game_status == 'dealer_turn':
        while 점수_계산(st.session_state.d_hand) < 17:
            st.session_state.d_hand.append(카드_뽑기())
        st.session_state.game_status = 'result'
        st.rerun()

    elif st.session_state.game_status == 'result':
        if not st.session_state.processed:
            딜_점, 딜_블 = 점수_계산(st.session_state.d_hand), 블랙잭_확인(st.session_state.d_hand)
            지급액, 승_수, 패_수 = 0, 0, 0
            결과_목록 = []
            for 핸디 in st.session_state.p_hands:
                내_점, 내_블 = 점수_계산(핸디), 블랙잭_확인(핸디)
                if 내_블:
                    if 딜_블: 지급 += st.session_state.bet; 결과 = "푸쉬"
                    else: 지급 += int(st.session_state.bet * 2.5); 결과 = "블랙잭"; 승_수 += 1
                elif 내_점 > 21: 결과 = "버스트"; 패_수 += 1
                elif 딜_점 > 21 or 내_점 > 딜_점: 지급 += st.session_state.bet * 2; 결과 = "승리"; 승_수 += 1
                elif 내_점 < 딜_점: 결과 = "패배"; 패_수 += 1
                else: 지급 += st.session_state.bet; 결과 = "푸쉬"
                결과_목록.append(결과)
            
            if 승_수 > 패_수: st.session_state.wins += 1
            elif 패_수 > 승_수: st.session_state.losses += 1
            else: st.session_state.draws += 1
            
            st.session_state.balance += 지급액
            st.session_state.history.append({"결과": ", ".join(결과_목록), "잔액": f"{st.session_state.balance:,}"})
            st.session_state.msg = " | ".join(결과_목록)
            st.session_state.processed = True
            st.rerun()
        
        if st.button("다음 게임") or st.session_state.auto_mode:
            if st.session_state.auto_mode: time.sleep(1.2)
            st.session_state.game_status = 'betting'
            st.rerun()
