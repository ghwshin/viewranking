import datetime
import re
import traceback

import requests
from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from bs4 import BeautifulSoup

from Control import countControl, searchControl
from blogKeywordInfo import blogKeywordInfo


class main_engine(QThread):
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

    def __init__(self):
        QThread.__init__(self)
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')
        self.keywordAndBlog = blogKeywordInfo()
        # count용 변수 (몇개 남았는가?)
        self.count = countControl()
        # url, header 등 검색 제어용 변수
        self.search = searchControl()
        # resultTable용
        self.rowcnt = 0

    def __del__(self):
        self.wait()

    def sleep(self, n):
        QtTest.QTest.qWait(n * 1000)

    def run(self):
        self.progressClear()
        while self.keywordAndBlog.current_size() != 0:
            try:
                self.keywordSearch()
            except FileNotFoundError:
                return
            except Exception as e:
                self.error_add(e)
                return
            self.progressChange()
        try:
            self.after_serach()
        except Exception as e:
            self.error_add(e)

    def error_add(self, err):
        self.addloglist(traceback.format_exc())
        self.addloglist('에러가 발생했습니다.')

    def addloglist(self, _str):
        self.addLog.emit(_str)
        self.afterAddLog.emit()

    def progressClear(self):
        self.count.setCountMax(self.keywordAndBlog.current_size())
        self.count.clearCounter()
        self.setProgressValue.emit(0)

    def progressChange(self):
        self.count.addCounter()
        self.setProgressValue.emit(self.count.count / self.count.countmax * 100)

    def set_current_keyword_indictor(self, keyword):
        self.setCurrentKeyword.emit(keyword)

    def set_keyword_remain_indictor(self, index):
        print_string = '현재 작업 수 / 남은 작업 수 : ' + str(index + 1) + ' / ' + str(self.count.countmax)
        self.setKeywordRemain.emit(print_string)

    def add_result_item_to_table_notcompany(self, keyword, blog_name, rank):
        self.increase_row()
        self.addResult.emit(self.rowcnt - 1, 0, keyword)
        # self.addResult.emit(self.rowcnt - 1, 1, blog_name)
        self.addResult.emit(self.rowcnt - 1, 1, self.ranklist_to_string(rank))

    """
    def add_result_item_to_table(self, company, keyword, rank):
        self.increase_row()
        self.addResult.emit(self.rowcnt - 1, 0, company)
        self.addResult.emit(self.rowcnt - 1, 1, keyword)
        self.addResult.emit(self.rowcnt - 1, 2, str(rank))
    """

    def ranklist_to_string(self, rank_list):
        _restr = str()
        for rank in rank_list:
            if rank != -1:
                _restr += (str(rank) + ",")
        return _restr[0:len(_restr) - 1]

    def increase_row(self):
        self.rowcnt += 1
        self.setRowValue.emit(self.rowcnt)

    # label 변경시 렉 줄이기
    def gui_event_pending_dismiss(self):
        if self.count.count % 100 == 0:
            self.clear_value.emit()
        QApplication.processEvents()
        self.label_repaint.emit()

    # delay 0.3초
    def internal_delay(self):
        self.sleep(0.3)

    def search_ui_refresh(self, i, target_keyword, target_name):
        _ui_str = "블로그 이름({}) - {}".format(target_name, target_keyword)
        self.set_current_keyword_indictor("검색 중인 키워드 : " + _ui_str)
        self.set_keyword_remain_indictor(i)
        self.addloglist(_ui_str + " 키워드 순위 검색")
        self.gui_event_pending_dismiss()

    def keywordSearch(self):
        current = self.keywordAndBlog.dequeue()
        target_name = current[0]
        current_keyword = current[1]
        self.search_ui_refresh(self.count.count, current_keyword, target_name)
        self.search.init_control()
        rank = self.rankfind(target_name, current_keyword)
        current[2] = rank
        self.keywordAndBlog.add_finish_job(current)

    def rankfind(self, target_name, target_keyword):
        self.search.clear_url()
        rank = list()
        while True:
            self.search.set_url(target_keyword)
            rank += self.find_rank(target_name)
            if self.search.isEnded == True and self.search.searchMaxCount != searchControl.UNCHANGED:
                break
            else:
                self.search.search_counting()
        #rank = list(set(rank))
        return rank

    # 검색후 url을 찾습니다.
    def find_rank(self, target_name):
        resource = requests.get(self.search.url, self.search.header)
        html_bs = BeautifulSoup(resource.text, 'html.parser')
        area = html_bs.find_all('a', {'class': '\\\"sub_txt'})
        self.update_max_count(html_bs)
        finded = [tag.text for tag in area]
        rank = self.url_blog_name_compare(target_name, finded)
        return rank

    def update_max_count(self, html_bs):
        if self.search.searchMaxCount == searchControl.UNCHANGED:
            try:
                self.search.searchMaxCount = int(html_bs.text[13:16])  # total 갯수 확인
            except:
                try:
                    self.search.searchMaxCount = int(html_bs.text[13:15])  # total 2자리
                except:
                    self.search.searchMaxCount = int(html_bs.text[13])  # total 1자리

    def url_blog_name_compare(self, target, names: list):
        rank = list()
        for rank_idx in range(len(names)):
            if target == names[rank_idx]:
                rank.append(rank_idx + self.search.searchCurrentCount)
        if not rank:
            rank.append(-1)
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

    def preprocess_sentence_kr(self, w):
        w = w.strip()
        w = re.sub(r"[^0-9가-힣?.!,¿]+", " ", w)  # \n도 공백으로 대체해줌
        w = w.strip()
        return w

    def after_serach(self):
        self.clearTable.emit()
        self.rowcnt = 0
        try:
            total_txt = './결과/통합순위_' + self.today + '.txt'
            with open(total_txt, 'w') as f:
                self.print_result_no_company(f)
        except Exception as e:
            self.error_add(traceback.format_exc())
            self.error_emit.emit('순위 결과를 쓰는 도중 문제가 발생했습니다.')
            return
        self.addloglist('모든 작업이 완료되었습니다.')

    def print_result_no_company(self, file):
        rank = list()
        before_keyword = ""
        for t in self.keywordAndBlog.get_finish_job_list():
            blog_name = t[0]
            keyword = t[1]
            if before_keyword == "":
                before_keyword = keyword
            elif before_keyword != keyword or self.keywordAndBlog.finish_list_empty():
                rank = list(set(rank))
                rank.sort()
                if rank:
                    before_keyword = self.preprocess_sentence_kr(before_keyword)
                    string = before_keyword + '\t' + self.ranklist_to_string(rank) + '\n'
                    file.write(string)
                    self.add_result_item_to_table_notcompany(before_keyword, blog_name, rank)
                before_keyword = keyword
                rank = list()
            for _rank in t[2]:
                if _rank > 0:
                    rank.append(_rank)
