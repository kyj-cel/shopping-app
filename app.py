import streamlit as st
import requests
import re

# 1. HTML 태그 제거 함수
def cleaning(raw_html):
    cleaner = re.compile("<.*?>") # 태그를 찾는 정석적인 방법으로 수정
    return re.sub(cleaner, '', raw_html)

# 2. 네이버 쇼핑 API 호출 함수
def search_naver_shopping(query, client_id, client_secret, display=20, sort='sim'):
    url = "https://openapi.naver.com/v1/search/shop.json"
    headers = {
        'X-Naver-Client-Id': client_id,
        "X-Naver-Client-Secret": client_secret
    }
    params = {
        'query': query,
        'display': display,
        'sort': sort
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        st.error(f'에러 발생: {response.status_code}')
        return None

# 3. Streamlit 페이지 설정
st.set_page_config(page_title='나만의 쇼핑검색기', page_icon="🛒", layout='wide')
st.title('🛒 나만의 네이버 쇼핑 검색앱')

# 4. 보안 설정 (비밀 금고에서 키 가져오기)
# 사용자가 직접 입력할 필요 없이 시스템 내부에서 자동으로 가져옵니다.
try:
    client_id = st.secrets["NAVER_CLIENT_ID"]
    client_secret = st.secrets["NAVER_CLIENT_SECRET"]
except:
    st.error("비밀 금고(Secrets) 설정을 확인해주세요! (관리자 설정 필요)")
    st.stop()

# 5. 사이드바 설정 (API 입력창이 사라지고 설정 도구만 남음)
with st.sidebar:
    st.header("⚙️ 검색 설정")
    
    sort_option = st.selectbox(
        '어떤 순서로 정렬할까요?',
        ('정확도순', '가격 낮은순', '가격 높은순', '최신순')
    )
    
    sort_dict = {
        '정확도순': 'sim',
        '가격 낮은순': 'asc',
        '가격 높은순': 'dsc',
        '최신순': 'date'
    }
    
    display_num = st.slider('보여줄 상품 개수', 10, 100, 20)
    st.markdown('---')
    st.info("API 연결 상태: 정상 ✅")

# 6. 메인 화면 검색창
query = st.text_input('🔍 사고 싶은 물건을 입력하세요.')

if st.button('검색하기', type='primary'):
    if not query:
        st.warning('검색어를 입력해주세요!')
    else:
        with st.spinner('네이버 쇼핑에서 찾는 중...'):
            items = search_naver_shopping(
                query,
                client_id,
                client_secret,
                display_num,
                sort=sort_dict[sort_option]
            )

            if items:
                st.success(f"'{query}' 검색 결과 {len(items)}개를 가져왔습니다!")
                
                cols = st.columns(4)
                for idx, item in enumerate(items):
                    with cols[idx % 4]:
                        st.image(item['image'], use_container_width=True)
                        # API 응답 필드인 mallName을 정확히 사용
                        st.caption(f"[{item.get('mallName', '정보없음')}]")
                        st.markdown(f"**{cleaning(item['title'])}**")

                        price = int(item['lprice'])
                        st.subheader(f'{price:,}원')
                        
                        st.link_button('상품 보러가기', item['link'], use_container_width=True)
                        st.markdown('---')
            else:
                st.info('결과가 없어요. 다른 검색어를 입력해 보세요.')