import datetime

import requests
from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from bs4 import BeautifulSoup

from Control import countControl, searchControl
from blogKeywordInfo import blogKeywordInfo


class main_thread(QThread):
    # class variable
    setProgressValue = pyqtSignal(int)
    addLog = pyqtSignal(str)
    afterAddLog = pyqtSignal()
    clear_value = pyqtSignal()
    setCurrentKeyword = pyqtSignal(str)
    setKeywordRemain = pyqtSignal(str)
    label_repaint = pyqtSignal()
    error_emit = pyqtSignal(str)

    # result Table 관련 signal
    setRowValue = pyqtSignal(int)
    clearTable = pyqtSignal()
    addResult = pyqtSignal(int, int, str)

    """
        blogKeywordInfo 클래스 설명
        companyList : 회사 리스트
        blogLinkList : dict 구조입니다.
        ex) blogLinkList['회사명'][0] : 회사의 첫번째 대상 링크 및 키워드
        실사용시, blogLinkList['회사명'][현재 처리 중인 순서][0] = 링크
        blogLinkList['회사명'][현재 처리 중인 순서][1] = 키워드
        22.03.25 추가
        1. 링크 -> 블로그 아이디로 교체
        2. 랭크를 list로 교체
        3. 랭크 크롤링을 다수로 변경
        
        22.04.01 변경
        1. 더이상 회사는 유효하지 않습니다. (삭제)
        2. blogLinkList를 list로 변경하였습니다.
        ([bid, keyword, rank])
    """

    def __init__(self):
        QThread.__init__(self)
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')
        self.keywordAndBlog = blogKeywordInfo()
        # count용 변수 (몇개 남았는가?)
        self.count = countControl()
        # url, header 등 검색 제어용 변수
        self.search = searchControl()

        # result : 0이면 찾지못함(누락됨)

        # resultTable용
        self.rowcnt = 0

    def __del__(self):
        self.wait()

    def sleep(self, n):
        QtTest.QTest.qWait(n * 1000)

    def run(self):
        self.count.setCountMax(len(self.keywordAndBlog.blogLinkList))
        self.keywordAndBlog.firstsize = self.keywordAndBlog.current_list_size()
        self.progressClear()
        while self.keywordAndBlog.current_list_size() != self.keywordAndBlog.cur:
            try:
                # 키워드 서칭
                self.keywordSearch()
            except FileNotFoundError:
                return
            except Exception as e:
                self.addloglist(str(e))
                self.addloglist('에러가 발생했습니다.')
                return
            self.progressChange()
        try:
            # 파일 저장
            self.after_serach()
        except Exception as e:
            self.addloglist(str(e))
            self.addloglist('에러가 발생했습니다.')

    def addloglist(self, str):
        self.addLog.emit(str)
        self.afterAddLog.emit()

    def progressClear(self):
        self.count.clearCounter()
        self.setProgressValue.emit(0)

    def progressChange(self):
        self.count.addCounter()
        self.setProgressValue.emit(self.count.count / self.count.countmax * 100)

    def set_current_keyword_indictor(self, keyword):
        self.setCurrentKeyword.emit(keyword)

    def set_keyword_remain_indictor(self, index, range):
        print_string = '현재 키워드 수 / 남은 키워드 수 : ' + str(index + 1) + ' / ' + str(range)
        self.setKeywordRemain.emit(print_string)

    def keywordSearch(self):
        # id, keyword, rank
        currentKeyword = self.keywordAndBlog.blogLinkList[self.keywordAndBlog.cur][1]
        self.addloglist(currentKeyword + " 키워드 순위 검색 시작")
        self.gui_event_pending_dismiss()

        targetLink = self.keywordAndBlog.blogLinkList[self.keywordAndBlog.cur][0]
        targetKeyword = self.keywordAndBlog.blogLinkList[self.keywordAndBlog.cur][1]
        self.search_ui_refresh(self.count.count, self.keywordAndBlog.firstsize, targetKeyword)
        self.search.init_control()
        rank = self.rankfind(targetLink, targetKeyword)
        # 랭크 설정!
        self.keywordAndBlog.blogLinkList[self.keywordAndBlog.cur][2] = rank

        self.keywordAndBlog.dequeue()

    def search_ui_refresh(self, i, linkrange, targetKeyword):
        self.set_current_keyword_indictor(targetKeyword)
        self.set_keyword_remain_indictor(i, linkrange)
        self.addloglist(targetKeyword + " 키워드 순위 검색 중")

    def rankfind(self, targetLink, targetKeyword):
        self.search.clear_url()
        before_rank = 0
        rank = 0
        while True:
            self.search.set_url(targetKeyword)
            if self.search.isEnded == True and self.search.searchMaxCount != 10000:
                break
            rank = self.findurl(targetLink)
            if rank > 0:
                self.search.isEnded = True
                break
            else:
                before_rank = -rank + before_rank
        # rank 누락상태
        if rank < 0:
            before_rank = 0
            rank = 0
        return before_rank + rank

    # 검색후 url을 찾습니다.
    def findurl(self, targetLink):
        resource = requests.get(self.search.url, self.search.header)
        html_bs = BeautifulSoup(resource.text, 'html.parser')
        area = html_bs.find_all('a', {'class': '\\"sub_thumb\\"'})
        if self.search.searchMaxCount == 10000:
            try:
                self.search.searchMaxCount = int(html_bs.text[14:17])  # total 갯수 확인
            except:
                try:
                    self.search.searchMaxCount = int(html_bs.text[14:16])  # total 2자리
                except:
                    self.search.searchMaxCount = int(html_bs.text[14])  # total 1자리
        find_url = [tag.get('href') for tag in area]  # url 따기
        rank = self.url_blog_compare(targetLink, find_url)
        return rank

    # url 대조 및 rank 확인 : rank를 찾으면 반환, 없으면 0
    def url_link_compare(self, target, urls):
        rank = 1
        target = target[:-13]  # target url 에서 게시물 고유 번호 제거
        for url in urls:
            url = url[2:len(url) - 2]  # url 분리
            if url == target:
                return rank
            rank += 1
        return -rank

    # url 대조 : 블로그 아이디로 대조
    def url_blog_compare(self, target, urls):
        rank = 1
        for url in urls:
            url = url[25:len(url) - 2]  # 블로그 아이디 분리
            if url == target:
                return rank
            rank += 1
        return -rank

    def after_serach(self):
        self.clearTable.emit()
        self.rowcnt = 0
        try:
            total_txt = './결과/통합순위_' + self.today + '.txt'
            with open(total_txt, 'w') as f:
                self.print_result_no_company(f)
                '''
                for company in self.keywordAndBlog.blogLinkList.keys():
                    self.print_result(company, f)
                '''
        except:
            self.error_emit.emit('순위 결과를 쓰는 도중 문제가 발생했습니다.')
            return
        self.addloglist('모든 작업이 완료되었습니다.')

    def print_result_no_company(self, file):
        for t in self.keywordAndBlog.blogLinkList:
            bid = t[0]
            keyword = t[1]
            rank = t[2]
            if rank != 0:
                string = keyword + '\t' + bid + '\t' + str(rank) + '\n'
                file.write(string)
                self.add_result_item_to_table(keyword, bid, rank)

    # 사용하지 않습니다.
    def print_result(self, company, file):
        company_txt = './결과/' + company + '_' + self.today + '.txt'
        with open(company_txt, 'w') as file_company:
            for i in range(self.keywordAndBlog.current_company_link_number(company)):
                link = self.keywordAndBlog.blogLinkList[company][i][0]
                keyword = self.keywordAndBlog.blogLinkList[company][i][1]
                rank = self.keywordAndBlog.blogLinkList[company][i][2]
                if rank == 0:
                    rank = '누락'
                string = company + '\t' + keyword + '\t' + link + '\t' + str(rank) + '\n'
                # log_string = company + '  ' + keyword + '  ' + link + '  ' + str(rank) + '  '
                file_company.write(string)
                file.write(string)
                self.add_result_item_to_table(company, keyword, rank)

    def add_result_item_to_table_notcompany(self, keyword, bid, rank):
        self.increase_row()
        self.addResult.emit(self.rowcnt - 1, 0, keyword)
        self.addResult.emit(self.rowcnt - 1, 1, bid)
        self.addResult.emit(self.rowcnt - 1, 2, str(rank))

    def add_result_item_to_table(self, company, keyword, rank):
        self.increase_row()
        self.addResult.emit(self.rowcnt - 1, 0, company)
        self.addResult.emit(self.rowcnt - 1, 1, keyword)
        self.addResult.emit(self.rowcnt - 1, 2, str(rank))

    def increase_row(self):
        self.rowcnt += 1
        self.setRowValue.emit(self.rowcnt)

    # label 변경시 렉 줄이기
    def gui_event_pending_dismiss(self):
        QApplication.processEvents()
        self.label_repaint.emit()

    # delay 0.3초
    def internal_delay(self):
        self.sleep(0.3)
