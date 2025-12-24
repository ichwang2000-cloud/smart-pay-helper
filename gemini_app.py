import streamlit as st
import google.generativeai as genai
import json 
import re 

# ==========================================
# [설정] API 키 입력
# ==========================================
MY_API_KEY = "AIzaSyDW-EPkfuT-X3dRlZLWlqKHaKulENWFDMY"

# 페이지 설정
st.set_page_config(page_title="스마트 수당 비서", page_icon="🚅", layout="centered")

# 세션 상태 초기화 (화면 전환용)
if 'page' not in st.session_state: st.session_state['page'] = 'input'
if 'result_text' not in st.session_state: st.session_state['result_text'] = ''

# --------------------------------------------------------------------------
# [디자인] 전문가용 프리미엄 스타일
# --------------------------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; font-family: 'Pretendard', sans-serif; }
    .main .block-container { max-width: 480px; padding: 0; background-color: white; min-height: 100vh; }
    .header-bar { background-color: #0054A6; padding: 20px; color: white; border-radius: 0 0 20px 20px; display: flex; justify-content: space-between; }
    .stButton > button[kind="primary"] { background-color: #0054A6 !important; border-radius: 12px; height: 3rem; font-weight: bold; width: 100%; }
    .stButton > button[kind="secondary"] { width: 100%; border-radius: 12px; }
    .result-box { background-color: #f1f3f5; border-radius: 15px; padding: 20px; border: 1px solid #dee2e6; user-select: text; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [함수] AI 연결
# --------------------------------------------------------------------------
if MY_API_KEY and "여기에" not in MY_API_KEY:
    genai.configure(api_key=MY_API_KEY)

def get_active_model():
    try:
        models = list(genai.list_models())
        m_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        return next((m for m in m_list if 'flash' in m), m_list[0])
    except: return None

# --------------------------------------------------------------------------
# [화면 1] 메인 입력 화면
# --------------------------------------------------------------------------
if st.session_state['page'] == 'input':
    # 상단 헤더 및 도움말 아이콘
    st.markdown("""<div class='header-bar'><span>🚅 스마트 수당 비서</span></div>""", unsafe_allow_html=True)
    
    col_empty, col_help = st.columns([0.8, 0.2])
    with col_help:
        with st.popover("❓"):
            st.markdown("""
            **📘 사용법**
            1. 캡처 이미지 업로드 또는 시간 입력
            2. 계산하기 버튼 클릭
            
            **🧮 로직**
            - 휴일1(8h): 1.5배
            - 휴일2(초과): 2.0배
            - 야간: 0.5배 가산
            """)

    with st.container(border=True):
        wage = st.number_input("나의 통상시급", value=23602, step=100)
        mode = st.radio("입력 방식", ["📸 이미지 분석", "⌨️ 직접 입력"], horizontal=True)
        
        img_data = None
        t_val, n_val = None, None
        
        if mode == "📸 이미지 분석":
            up_file = st.file_uploader("다이아 캡처 첨부", type=["jpg","png","jpeg"], label_visibility="collapsed")
            if up_file:
                st.image(up_file)
                img_data = {'mime_type': up_file.type, 'data': up_file.getvalue()}
        else:
            c1, c2 = st.columns(2)
            t_val = c1.text_input("총 시간", placeholder="11:25")
            n_val = c2.text_input("야간 시간", placeholder="30분")

    if st.button("계산 결과 확인하기 🚀", type="primary"):
        model_name = get_active_model()
        if not model_name: st.error("API 연결 확인 필요")
        else:
            with st.spinner("AI 분석 중..."):
                model = genai.GenerativeModel(model_name)
                prompt = f"시급 {wage}원, 입력값({t_val}, {n_val}). 상세 계산 내역을 이미지 예시처럼 친절하게 설명하고 마지막엔 ### 총합: [금액]원 형태로 끝내줘."
                content = [img_data, prompt] if img_data else [prompt]
                res = model.generate_content(content)
                st.session_state['result_text'] = res.text
                st.session_state['page'] = 'result'
                st.rerun()

# --------------------------------------------------------------------------
# [화면 2] 결과 확인 화면
# --------------------------------------------------------------------------
else:
    if st.button("⬅️ 홈으로 가기"):
        st.session_state['page'] = 'input'
        st.rerun()

    st.markdown("### 📝 상세 계산 내역")
    # AI 결과를 예쁜 상자 안에 출력 (복사 가능)
    st.markdown(f"<div class='result-box'>{st.session_state['result_text']}</div>", unsafe_allow_html=True)
    
    st.divider()
    with st.expander("📋 전체 텍스트 복사"):
        st.code(st.session_state['result_text'], language=None)
    
    if st.button("🔄 초기화 후 다시 하기", type="secondary"):
        st.session_state['page'] = 'input'
        st.rerun()
