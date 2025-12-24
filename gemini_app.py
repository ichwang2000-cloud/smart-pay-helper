import streamlit as st
import google.generativeai as genai
import json 
import re 

# ==========================================
# [설정] API 키 입력
# ==========================================
MY_API_KEY = "AIzaSyDW-EPkfuT-X3dRlZLWlqKHaKulENWFDMY"

# 페이지 설정
st.set_page_config(
    page_title="스마트 수당 비서", 
    page_icon="",
    layout="centered"
)

# --------------------------------------------------------------------------
# [상태 관리] 화면 전환용 세션 상태 초기화
# --------------------------------------------------------------------------
if 'page' not in st.session_state:
    st.session_state['page'] = 'input'
if 'result_text' not in st.session_state:
    st.session_state['result_text'] = ''

# --------------------------------------------------------------------------
# [디자인] UX 전문가용 프리미엄 CSS
# --------------------------------------------------------------------------
def apply_premium_style():
    st.markdown("""
        <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        
        /* 전체 배경 및 폰트 */
        .stApp { background-color: #F8F9FB; font-family: 'Pretendard', sans-serif; }
        
        /* 모바일 앱 카드 컨테이너 */
        .main .block-container {
            max-width: 480px; padding: 0; margin: 0 auto;
            background-color: white; min-height: 100vh;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }
        
        /* 헤더 디자인 */
        .app-header {
            background-color: #0054A6; padding: 20px;
            display: flex; justify-content: space-between; align-items: center;
            color: white; border-radius: 0 0 25px 25px;
            margin-bottom: 20px;
        }
        
        /* 카드형 섹션 */
        .content-card {
            padding: 20px; margin: 0 15px 20px 15px;
            background: white; border-radius: 20px;
            border: 1px solid #F0F0F0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        
        /* 버튼 스타일 */
        .stButton > button {
            width: 100%; border-radius: 15px !important;
            padding: 12px 0 !important; font-size: 1rem !important;
            font-weight: 600 !important; transition: 0.3s;
        }
        .stButton > button[kind="primary"] {
            background-color: #0054A6 !important; color: white !important; border: none;
        }
        .stButton > button[kind="secondary"] {
            background-color: #F0F2F6 !important; color: #333 !important; border: none;
        }
        
        /* 결과 설명 박스 (복사 가능하도록 설정) */
        .explanation-box {
            background-color: #FFFFFF; border: 1px solid #E9ECEF;
            border-radius: 15px; padding: 20px; line-height: 1.7;
            color: #333; font-size: 0.95rem; user-select: text;
        }
        
        header, footer, .stDeployButton { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

apply_premium_style()

# --------------------------------------------------------------------------
# [로직] AI 및 계산 함수
# --------------------------------------------------------------------------
if MY_API_KEY and "여기에" not in MY_API_KEY:
    genai.configure(api_key=MY_API_KEY)

def get_model():
    try:
        models = list(genai.list_models())
        vision_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods and ('vision' in m.name or 'flash' in m.name)]
        for m in vision_models:
            if 'flash' in m: return m
        return vision_models[0] if vision_models else None
    except: return None

# --------------------------------------------------------------------------
# [화면 1] 입력 화면 (Input Page)
# --------------------------------------------------------------------------
if st.session_state['page'] == 'input':
    # 상단 바 (도움말 아이콘 포함)
    col_t, col_h = st.columns([0.85, 0.15])
    with col_t:
        st.markdown("<h3 style='margin:15px 0 0 20px; color:#0054A6;'>🚅 스마트 수당 비서</h3>", unsafe_allow_html=True)
    with col_h:
        if st.button("❓", help="도움말 보기"):
            st.toast("하단의 도움말 섹션을 확인하세요!")

    st.markdown("<p style='margin-left:20px; font-size:0.9rem; color:#666;'>AI 가 스마트하게 계산해주는 초과수당 계산기 입니다.</p>", unsafe_allow_html=True)

    with st.container():
        # 시급 설정
        st.markdown("<div style='margin: 0 20px;'>", unsafe_allow_html=True)
        wage = st.number_input("💵 나의 통상시급 (원)", value=23602, step=100, format="%d")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 입력 방식 선택
        mode = st.tabs(["📸 캡처 업로드", "⌨️ 직접 입력"])
        
        image_data = None
        m_total, m_night = None, None
        
        with mode[0]:
            st.caption("(승무다이아 조회 또는 개인근무 명세서 화면)")
            uploaded_file = st.file_uploader("파일 선택", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
            if uploaded_file:
                st.image(uploaded_file, use_column_width=True)
                image_data = {'mime_type': uploaded_file.type, 'data': uploaded_file.getvalue()}
                
        with mode[1]:
            c1, c2 = st.columns(2)
            m_total = c1.text_input("총 근무 시간", placeholder="예: 11:25")
            m_night = c2.text_input("야간 시간", placeholder="예: 30분")
            st.caption("※ '11시간 25분' 등 자유롭게 입력 가능")

    # 계산 버튼
    st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
    if st.button("계산하기 🚀", type="primary", use_container_width=True):
        active_model = get_model()
        if not active_model:
            st.error("AI 연결에 실패했습니다. API 키를 확인하세요.")
        elif not image_data and not m_total:
            st.warning("데이터를 입력해주세요.")
        else:
            with st.spinner("AI 전문가가 분석 중입니다..."):
                try:
                    model = genai.GenerativeModel(active_model)
                    content = [image_data] if image_data else []
                    prompt = f"""
                    당신은 수당 정산 전문가입니다. 아래 데이터를 분석하여 상세 내역을 작성하세요.
                    시급: {wage}원 / 직접입력: 총시간({m_total}), 야간({m_night})
                    
                    [계산 규칙] 휴일1(8시간까지 1.5배), 휴일2(8시간초과 2.0배), 야간(0.5배 가산)
                    [작성 스타일] 정중한 존댓말로 항목별 상세 계산 과정을 풀어서 작성하세요. 
                    금액엔 반드시 콤마를 붙이고, 최종 합계는 맨 마지막에 ### 총합: [금액]원 형태로 강조하세요.
                    이미지의 '휴게시간'을 찾아 실 근무시간에서 제외하는 센스를 발휘하세요.
                    """
                    content.append(prompt)
                    response = model.generate_content(content)
                    
                    # 결과 저장 및 페이지 전환
                    st.session_state['result_text'] = response.text
                    st.session_state['page'] = 'result'
                    st.rerun()
                except Exception as e:
                    st.error(f"오류 발생: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 하단 도움말
    with st.expander("❓ 사용법 및 로직 안내"):
        st.markdown(f"""
        **1. 사용 방법**
        * 승무다이아 조회 화면을 캡처하여 업로드하거나, 총 시간/야간 시간을 직접 입력하세요.
        * '계산하기'를 누르면 AI가 휴게시간 등을 고려하여 수당을 산출합니다.
        
        **2. 계산 기본 로직**
        * **휴일1**: 실 근무 8시간까지 **{int(wage*1.5):,}원**(1.5배) 적용
        * **휴일2**: 8시간 초과분 **{int(wage*2.0):,}원**(2.0배) 적용
        * **야간가산**: 22시~06시 사이 근무 시 **{int(wage*0.5):,}원**(0.5배) 중복 가산
        """)

# --------------------------------------------------------------------------
# [화면 2] 결과 화면 (Result Page)
# --------------------------------------------------------------------------
else:
    # 상단 바 (홈 버튼)
    col_back, col_title = st.columns([0.2, 0.8])
    with col_back:
        if st.button("🏠 홈"):
            st.session_state['page'] = 'input'
            st.rerun()
    with col_title:
        st.markdown("<h3 style='margin-top:5px; color:#0054A6;'>📝 분석 결과</h3>", unsafe_allow_html=True)

    st.markdown("<div class='content-card'>", unsafe_allow_html=True)
    
    # 텍스트 에어리어 대신 일반 마크다운으로 출력하되, 선택/복사 가능하도록 표시
    # 유저가 언급한 </div> 태그 오류 방지를 위해 strip() 처리
    clean_result = st.session_state['result_text'].strip()
    st.markdown(f"""
    <div class="explanation-box">
        {clean_result.replace("**", "<b>").replace("* ", "• ").replace("\n", "<br>")}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 복사용 텍스트 제공
    with st.expander("📋 텍스트 복사하기"):
        st.code(clean_result, language=None)

    if st.button("새로 계산하기 🔄", use_container_width=True):
        st.session_state['page'] = 'input'
        st.rerun()