import streamlit as st
import requests
import re

def cleaning(raw_html):
    cleaner=re.compile("<*.?>")
    return re.sub(cleaner,'',raw_html)
def search_naver_shopping(query,client_id,client_secret,display=20,sort='sim'):
    url="https://openapi.naver.com/v1/search/shop.json"
    headers= {
        'X-Naver-Client-Id':client_id,
        "X-Naver-Client-Secret":client_secret
    }
    params={
        'query':query,
        'display':display,
        'sort':sort
    }
    response=requests.get(url,headers=headers,params=params)
    if response.status_code==200:
        return response.json().get('items',[])
    else:
        st.error(f'에러발생:{response.status_code}')
        return None
st.set_page_config(page_title='나만의 쇼핑검색기',page_icon="🛒",layout='wide')
st.title('🛒나만의 네이버 쇼핑 검색앱')

with st.sidebar:
    st.header("설정")
    client_id=st.text_input("네이버 client id",type='password')
    client_secret = st.text_input("Client Secret 입력", type="password")
    
    st.markdown('---')

    sort_option=st.selectbox(
        '어떤 순서로 정렬할까요?',
        ('정확도순','가격 낮은순','가격 높은순','최신순')
    )
    sort_dict={
        '정확도순':'sim',
        '가격 낮은순':'asc',
        '가격 높은순':'dsc',
        '최신순':'date'
    }
    display_num=st.slider('보여줄 상품 개수',10,100,20)

query=st.text_input('사고싶은 물건을 입력하세요.')
if st.button('검색하기',type='primary'):
    if not client_id or not client_secret:
        st.warning('왼쪽 사이드바에 API 키를 넣어주세요!')
    elif not query:
        st.warning('검색어를 입력해주세요')
    else:
        with st.spinner('네이버 쇼핑에서 찾는중...'):
            items=search_naver_shopping(
                query,
                client_id,
                client_secret,
                display_num,
                sort=sort_dict[sort_option]
            )

            if items:
                st.success(f'{query} 검색결과 {len(items)}개를 가져왔습니다!')
                cols=st.columns(4)
                for idx,item in enumerate(items):
                    with cols[idx%4]:
                        st.image(item['image'],use_container_width=True)
                        st.caption(f'[{item['mallname']}]')
                        st.markdown(f'**{cleaning(item['title'])}**')

                        price=int(item['lprice'])
                        st.subheader(f'{price:,}원')
                        st.link_button('상품보러가기',item['link'],use_container_width=True)
                        st.markdown('---')
            else:
                st.info('결과가 없어요. 다른것으로 검색해보세요.')
