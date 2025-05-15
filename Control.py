import re
import time

import requests
from bs4 import BeautifulSoup

import Control


def get_request_from_url(target_url):
    try_num = 0
    response = None
    while try_num < 5:
        try:
            response = requests.get(target_url, headers=searchControl.HEADER)
            # 25.05.14 : Request 실패 시 재시도 추가
            if response.status_code != 200:
                print("Request Error : " + str(response.status_code))
                raise Exception("Request Error : " + str(response.status_code))
        except:
            try_num += 1
            time.sleep(1)
            continue
        break
    return response

class countControl:
    def __init__(self):
        self.count = 0
        self.countmax = 0

    def setCountMax(self, maxnumber):
        self.countmax = maxnumber

    def addCounter(self):
        self.count += 1

    def clearCounter(self):
        self.count = 0


class searchControl:
    # 24.02.04 : view -> 블로그 탭으로 명칭 변경됨
    # 해당 건 이후 api 쿼리가 암호화? 또는 다른 방식으로 변경된 것으로 보임

    # 24.02.08 : 쿼리 개인화 결과인 enlu_query를 가져오는 방법을 구현
    UNCHANGED = 10000
    NONEXTURL = 10001
    AVALIABLEURL = 10002

    QUERY_BLOG_URL = "https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query="
    QUERY_SEARCH_URL = "https://search.naver.com/search.naver?ssc=tab.nx.all&where=nexearch&sm=tab_jum&query="
    POSTFIX_BLOG = "&abt="
    POSTFIX_SEARCH = "&amp;abt="
    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        "Accept": """text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7""",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Referer": 'http://naver.com'
    }

    def __init__(self):
        # 24.12.27 : api url 변경 (탭 순서 변경됨)
        self.urlPrefix = "https://s.search.naver.com/p/review/49/search.naver?ssc=tab.m_blog.all&api_type=7"
        self.native_naver_url = "https://search.naver.com/search.naver?sm=tab_hty.top&ssc=tab.blog.all"
        self.enlu_query = ""
        self.urlQueryPart = '&query='
        self.urlStartPart = "&start="
        self.url = self.urlPrefix + self.urlStartPart + str(1) + self.urlQueryPart

        self.isAllSerach = True
        self.isEnded = False
        self.is_enlu_query = True

        self.nextSearchStatus = self.UNCHANGED
        self.searchCurrentCount = 1

    def set_url(self, keyword):
        self.clear_url()
        self.url += keyword
        self.url += self.enlu_query

    def extract_enlu_query(self, html_text):
        """25.05.14 : URL에서 enlu_query 파라미터 값을 추출하는 함수"""
        ret = ''
        try:
            pattern = re.compile(r'&enlu_query=(.*?)&abt=')
            match = pattern.search(html_text)

            if match:
                ret = match.group(1)
            else:
                # 백업 패턴: abt 파라미터가 없을 경우를 대비
                backup_pattern = re.compile(r'&enlu_query=(.*?)&(?:enqx_theme|[a-z]+)=')
                backup_match = backup_pattern.search(html_text)

                if backup_match:
                    ret = backup_match.group(1)

            ret = '&enlu_query=' + ret
            return ret
        except Exception as e:
            print(f"enlu_query 추출 중 오류 발생: {e}")
            return ret

    def get_enlu_query(self, target, url, find_postfix):
        # 24.02.08 : enlu_query를 가져오는 방법
        # blog 탭으로 처음 처리하고 실패하면 일반 검색창을 이용함
        target_url = url + target
        response = Control.get_request_from_url(target_url)
        # 24.04.28 : 접속 실패시 재시도 추가
        if response is None:
            return False
        html_bs = BeautifulSoup(response.text, "html.parser")
        self.enlu_query = self.extract_enlu_query(str(html_bs))

        if self.enlu_query == '':
            # 찾는데 실패하면 일반 검색창 확인
            if url == self.QUERY_BLOG_URL:
                self.get_enlu_query(target, self.QUERY_SEARCH_URL, self.POSTFIX_SEARCH)
            else:
                return False
        return True

    def search_counting(self):
        if self.isAllSerach:
            # if self.searchCurrentCount + 30 >= self.nextSearchStatus:
            if self.nextSearchStatus == self.NONEXTURL:
                self.isEnded = True
            self.searchCurrentCount += 30
        else:
            self.isEnded = True

    def clear_url(self):
        self.url = self.urlPrefix + self.urlStartPart + str(self.searchCurrentCount) + self.urlQueryPart

    def init_control(self, keyword):
        # self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart
        self.url = self.urlPrefix + self.urlStartPart + str(1) + self.urlQueryPart
        self.isEnded = False
        self.nextSearchStatus = self.UNCHANGED
        self.searchCurrentCount = 1
        if not self.get_enlu_query(keyword, self.QUERY_BLOG_URL, self.POSTFIX_BLOG):
            self.is_enlu_query = False
        else:
            self.is_enlu_query = True

    def clear_maxcount(self):
        self.nextSearchStatus = self.UNCHANGED
