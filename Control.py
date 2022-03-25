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
    def __init__(self):
        self.header = {'User-Agent': 'Mozilla/5.0', 'referer': 'http://naver.com'}
        self.urlQueryPart = '&query='
        self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart

        self.isAllSerach = True
        self.isEnded = False

        self.searchMaxCount = 10000
        self.searchCurrentCount = 1

        self.searchRankMaxCount = 50

    def set_url(self, keyword):
        self.clear_url()
        self.url += keyword
        if self.isAllSerach == True:
            if self.searchCurrentCount + 30 >= self.searchMaxCount:
                self.searchCurrentCount = 1
                self.isEnded = True
            else:
                self.searchCurrentCount += 30
        else:
            self.isEnded = True

    def clear_url(self):
        self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=' + str(self.searchCurrentCount) + self.urlQueryPart

    def init_control(self):
        self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart
        self.isEnded = False
        self.searchMaxCount = 10000
        self.searchCurrentCount = 1

    def clear_maxcount(self):
        self.searchMaxCount = 10000