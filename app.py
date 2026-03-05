import streamlit as st
import requests
import re
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------
# 1. 파이어베이스 초기화
# ---------------------------------------------------------
if not firebase_admin._apps:
    try:
        # secrets.toml의 [firebase] 섹션 전체를 가져옵니다.
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"파이어베이스 초기화 실패: {e}")
        st.stop()

db = firestore.client()

# FIREBASE_WEB_API_KEY가 secrets에 있는지 확인
if "FIREBASE_WEB_API_KEY" in st.secrets:
    FIREBASE_WEB_API_KEY = st.secrets["FIREBASE_WEB_API_KEY"]
else:
    st.error("secrets.toml에 FIREBASE_WEB_API_KEY가 없습니다!")
    st.stop()

# ---------------------------------------------------------
# 2. 핵심 기능 함수
# ---------------------------------------------------------
def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload)

def sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    return requests.post(url, json=payload)

def cleaning(raw_html):
    cleaner = re.compile("<.*?>")
    return re.sub(cleaner, '', raw_html)

def search_naver_shopping(query, client_id, client_secret):
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {'X-Naver-Client-Id': client_id, "X-Naver-Client-Secret": client_secret}
    params = {'query': query, 'display': 20, 'sort': 'sim'}
    res = requests.get(url, headers=headers, params=params)
    return res.json().get('items', []) if res.status_code == 200 else None

def add_to_wishlist(uid, item):
    # productId가 없을 경우를 대비해 고유한 ID 생성
    p_id = item.get('productId') or str(hash(item['link']))
    try:
        doc_ref = db.collection('users').document(uid).collection('wishlist').document(p_id)
        doc_ref.set({
            'title': cleaning(item['title']),
            'image': item['image'],
            'lprice': item['lprice'],
            'link': item['link'],
            'mallName': item.get('mallName', '정보없음')
        })
        return True
    except Exception as e:
        st.error(f"찜하기 저장 실패: {e}")
        return False

# ---------------------------------------------------------
# 3. 화면 UI 구성
# ---------------------------------------------------------
st.set_page_config(page_title='나만의 쇼핑검색기', page_icon="🛒", layout='wide')

if 'user' not in st.session_state:
    st.session_state['user'] = None

if st.session_state['user'] is None:
    st.title('🔒 로그인 및 회원가입')
    t1, t2 = st.tabs(["로그인", "회원가입"])
    with t1:
        e = st.text_input("이메일", key="l_e")
        p = st.text_input("비밀번호", type="password", key="l_p")
        if st.button("로그인", type="primary"):
            r = sign_in(e, p)
            if r.status_code == 200:
                st.session_state['user'] = r.json()
                st.rerun()
            else: st.error("로그인 실패!")
    with t2:
        ne = st.text_input("새 이메일", key="s_e")
        np = st.text_input("비밀번호 (6자 이상)", type="password", key="s_p")
        if st.button("가입하기"):
            r = sign_up(ne, np)
            if r.status_code == 200: st.success("가입 성공! 로그인해주세요.")
            else: st.error("가입 실패!")

else:
    uid = st.session_state['user']['localId']
    
    with st.sidebar:
        st.write(f"👤 {st.session_state['user']['email']}님")
        if st.button("로그아웃"):
            st.session_state.clear() # 모든 정보 초기화
            st.rerun()
        menu = st.radio("메뉴", ["🔍 쇼핑 검색", "❤️ 내 찜 목록"])

    # 메뉴 1: 검색
    if menu == "🔍 쇼핑 검색":
        st.title('🛒 쇼핑 검색')
        q = st.text_input('🔍 검색어를 입력하세요.')
        if st.button('검색하기', type='primary') and q:
            items = search_naver_shopping(q, st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"])
            st.session_state['search_results'] = items

        if 'search_results' in st.session_state and st.session_state['search_results']:
            cols = st.columns(4)
            for i, item in enumerate(st.session_state['search_results']):
                with cols[i % 4]:
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{cleaning(item['title'])}**")
                    st.subheader(f"{int(item['lprice']):,}원")
                    
                    c1, c2 = st.columns(2)
                    c1.link_button('보러가기', item['link'], use_container_width=True)
                    # 찜하기 버튼
                    p_id = item.get('productId') or f"idx_{i}"
                    if c2.button('❤️ 찜', key=f"btn_{p_id}", use_container_width=True):
                        if add_to_wishlist(uid, item):
                            st.toast('찜 목록에 추가되었습니다! ❤️')

    # 메뉴 2: 찜 목록
    elif menu == "❤️ 내 찜 목록":
        st.title('❤️ 내 찜 목록')
        docs = db.collection('users').document(uid).collection('wishlist').stream()
        wish_items = [doc.to_dict() for doc in docs]
        
        if not wish_items:
            st.info("찜한 상품이 없습니다.")
        else:
            cols = st.columns(4)
            for i, item in enumerate(wish_items):
                with cols[i % 4]:
                    st.image(item['image'], use_container_width=True)
                    st.markdown(f"**{item['title']}**")
                    st.subheader(f"{int(item['lprice']):,}원")
                    st.link_button('보러가기', item['link'], use_container_width=True)