import streamlit as st
import google.generativeai as genai
import json
import re

# 페이지 설정 (가장 상단에 위치)
st.set_page_config(page_title="스마트 수당 비서", page_icon="🚅", layout="centered")

# --------------------------------------------------------------------------
# [보안] st.secrets에서 API 키 불러오기
# --------------------------------------------------------------------------
# 로컬 테스트 시에는 .streamlit/secrets.toml 파일에 저장하고,
# 배포 시에는 Streamlit Cloud 설정의 Secrets 섹션에 저장해야 합니다.
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ API 키(GEMINI_API_KEY)가 설정되지 않았습니다. 관리자 설정을 확인하세요.")
    st.stop()

# --------------------------------------------------------------------------
# [상태 관리] 화면 전환용 세션 상태 초기화
# --------------------------------------------------------------------------
if 'page' not in st.session_state: st.session_state['page'] = 'input'
if 'result_text' not in st.session_state: st.session_state['result_text'] = ''

# --------------------------------------------------------------------------
# [디자인] UX 전문가용 프리미엄 스타일
# --------------------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    .stApp { background-color: #F8F9FB; font-family: 'Pretendard', sans-serif; }
    .main .block-container { max-width: 480px; padding: 0; background-color: white; min-height: 100vh; box-shadow: 0 0 20px rgba(0,0,0,0.05); }
    .header-bar { background-color: #0054A6; padding: 20px; color: white; border-radius: 0 0 20px 20px; display: flex; justify-content: space-between; align-items: center; }
    .stButton > button[kind="primary"] { background-color: #0054A6 !important; border-radius: 12px; height: 3.2rem; font-weight: bold; width: 100%; color: white !important; }
    .stButton > button[kind="secondary"] { width: 100%; border-radius: 12px; background-color: #F0F2F6 !important; border: none; }
    .result-box { background-color: #f1f3f5; border-radius: 15px; padding: 25px; border: 1px solid #dee2e6; user-select: text; line-height: 1.7; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# [로직] AI 모델 및 연결 설정
# --------------------------------------------------------------------------
genai.configure(api_key=MY_API_KEY)

def get_active_model():
    try:
        models = list(genai.list_models())
        m_list = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        # flash 모델 우선 사용
        return next((m for m in m_list if 'flash' in m), m_list[0])
    except: return None

# --------------------------------------------------------------------------
# [화면 1] 메인 입력 화면 (Input Page)
# --------------------------------------------------------------------------
if st.session_state['page'] == 'input':
    st.markdown("<div class='header-bar'><span style='font-size:1.2rem; font-weight:bold;'>🚅 스마트 수당 비서</span></div>", unsafe_allow_html=True)
    
    # 상단 도움말 팝오버
    col_e, col_h = st.columns([0.85, 0.15])
    with col_h:
        with st.popover("❓"):
            st.markdown("""
            **📘 사용법**
            1. 캡처 이미지 업로드 또는 시간 입력
            2. '계산 결과 확인하기' 클릭
            
            **🧮 계산 로직**
            - **휴일1(8h)**: 1.5배 적용
            - **휴일2(초과)**: 2.0배 적용
            - **야간가산**: 0.5배 가산 중복 적용
            """)

    st.markdown("<div style='padding: 0 20px;'>", unsafe_allow_html=True)
    
    # 입력 컨테이너
    with st.container(border=True):
        wage = st.number_input("💵 나의 통상시급 (원)", value=23602, step=100)
        input_mode = st.segmented_control("입력 방식", ["📸 이미지", "⌨️ 직접 입력"], default="📸 이미지")
        
        img_data = None
        t_val, n_val = None, None
        
        if input_mode == "📸 이미지":
            up_file = st.file_uploader("이미지 업로드", type=["jpg","png","jpeg"], label_visibility="collapsed")
            if up_file:
                st.image(up_file, use_column_width=True)
                img_data = {'mime_type': up_file.type, 'data': up_file.getvalue()}
        else:
            c1, c2 = st.columns(2)
            t_val = c1.text_input("총 근무시간", placeholder="예: 11:25")
            n_val = c2.text_input("야간 시간", placeholder="예: 30분")
            st.caption("※ '11시간 20분', '11.3' 등 자유로운 형식 지원")

    # 계산 실행 버튼
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    if st.button("계산 결과 확인하기 🚀",
