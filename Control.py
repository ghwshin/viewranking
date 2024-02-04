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
    UNCHANGED = 10000
    NONEXTURL = 10001
    AVALIABLEURL = 10002
    def __init__(self):
        self.header = {'User-Agent': 'Mozilla/5.0', 'referer': 'http://naver.com'}
        # self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart
        self.urlPrefix = "https://s.search.naver.com/p/review/47/search.naver?ssc=tab.blog.all&api_type=4"
        self.urlSuffix = "&enlu_query=IggCACyAULgRAAAAtdoURqXUdp9ygLuVMM8qJuGb919ekLoOUdX4%2BBeeSh702x4qXTBxPwtc%2BQFzSTZ4YsuNjWhH44SV%2B2Qz3rgw3BVC74f2Dr9mYX89v8e8eeY6ePDDEKVJSf7lD5IEU0BGfOMj3WLM3re5lU6nK%2F6Qzigk3FEemtwKcep4Fep2ELZstOZFKgpfAx6gJrSnwaQop6OC%2BQ%2B18vjhw2OYUef72%2Bx874S%2FJjgiUxIwjKvvCXa8yrclSmG70rX51pdKBeT4oXJGNtkO%2FwtL%2FxPeMaZTEHGKBXBLSFOVS9GY0HFOUn9vGCnemasQ74CG00S5zvttYOi%2BZFAFxF3xoUxH%2B5Y52QPrtWkGQjw7oDJ3b78HYDBvlk6G32%2FF8vgZWXBoExJ58EriU94g10Z0AsMRkL%2FOkRwg%2BOsYWuR%2FzJ5%2FoyViMBMYp4HZ9E8%2BcutbK7GNs7olLeozmj65Myc9mfClpM4BtR5Pdpp1aix%2FbC%2Bqp1%2FdZ4v%2BQtyAFrqP3rDGB%2BCE%2FdQRrtXkuUOaXd%2BOPayzdRmYFJzusMyo3oKrDiULWZ8x%2BjQiYzgNY7evFQO1Xfz2JYxCKnFQ4e%2FQo4pwBEKtAS2kCo74pTUqZ7uIedLLo8ieI3D5HMi2aaQA4y04OamAIadAozKsI0oet2ZXgd3hklTvMywh239p%2FIwht1%2F4HE0luJlio7Be%2B7AiV67z8P4ZFm7K"
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
        self.url += self.urlSuffix

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
        # self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=' + str(
        #     self.searchCurrentCount) + self.urlQueryPart

    def init_control(self):
        # self.url = 'https://s.search.naver.com/p/review/search.naver?rev=44&where=view&api_type=11&start=1' + self.urlQueryPart
        self.url = self.urlPrefix + self.urlStartPart + str(1) + self.urlQueryPart
        self.isEnded = False
        self.nextSearchStatus = self.UNCHANGED
        self.searchCurrentCount = 1

    def clear_maxcount(self):
        self.nextSearchStatus = self.UNCHANGED
