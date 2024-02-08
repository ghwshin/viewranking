import requests
from bs4 import BeautifulSoup


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
    def __init__(self):
        self.header = {'User-Agent': 'Mozilla/5.0', 'referer': 'http://naver.com'}
        # self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart
        self.urlPrefix = "https://s.search.naver.com/p/review/47/search.naver?ssc=tab.blog.all&api_type=4"
        self.enlu_query = ""
        self.urlQueryPart = '&query='
        self.urlStartPart = "&start="
        self.url = self.urlPrefix + self.urlStartPart + str(1) + self.urlQueryPart

        self.isAllSerach = True
        self.isEnded = False

        self.nextSearchStatus = self.UNCHANGED
        self.searchCurrentCount = 1

    def set_url(self, keyword):
        self.clear_url()
        self.url += keyword
        self.url += self.enlu_query

    def get_enlu_query(self, target):
        # 24.02.08 : enlu_query를 가져오는 방법
        url = "https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query="
        url += target
        response = requests.get(url, headers=self.header)
        html_bs = BeautifulSoup(response.text, "html.parser")
        enlu_query = "&" + str(html_bs)[
                           str(html_bs).find("enlu_query"):str(html_bs).find("&abt=&_callback=getBlogContents")]
        print(enlu_query)
        self.enlu_query = enlu_query

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
        self.get_enlu_query(keyword)

    def clear_maxcount(self):
        self.nextSearchStatus = self.UNCHANGED
