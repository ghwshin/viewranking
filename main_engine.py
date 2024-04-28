import datetime
import re
import traceback

import requests
from PyQt5 import QtTest
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from bs4 import BeautifulSoup

import Control
from Control import countControl, searchControl
from ExcelControl import ExcelControl
from blogKeywordUrls import blogKeywordUrls


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
        # self.keywordAndBlog = blogKeywordInfo()
        self.keywordAndBlog = blogKeywordUrls()
        self.excel = ExcelControl("템플릿.xlsx")
        # count용 변수 (몇개 남았는가?)
        self.count = countControl()
        # url, header 등 검색 제어용 변수
        self.search = searchControl()
        # resultTable용
        self.rowcnt = 0
        # 순위 제한 변수
        self.rankLimits = 0

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
                self.error_add()
                return
            self.progressChange()
        try:
            # 23.06.28
            # self.after_serach()
            self.print_in_excel()
        except Exception as e:
            self.error_add()

    def error_add(self):
        self.error_emit.emit(traceback.format_exc())
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

    def add_result_item_to_table_notcompany(self, keyword, urls, rank):
        self.increase_row()
        self.addResult.emit(self.rowcnt - 1, 0, keyword)
        self.addResult.emit(self.rowcnt - 1, 1, urls)
        if rank != -1:
            self.addResult.emit(self.rowcnt - 1, 2, str(rank))
        # self.addResult.emit(self.rowcnt - 1, 2, self.ranklist_to_string(rank))

    def ranklist_to_string(self, rank_list):
        _restr = str()
        for rank in rank_list:
            if rank != -1:
                _restr += (str(rank) + ",")
            else:
                _restr = ","
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

    def search_ui_refresh(self, i, target_keyword, target_url):
        # _ui_str = "블로그 이름({}) - {}".format(target_url, target_keyword)
        _ui_str = "{} 검색 중...".format(target_keyword)
        self.set_current_keyword_indictor("검색 중인 키워드 : " + _ui_str)
        self.set_keyword_remain_indictor(i)
        self.addloglist(_ui_str + " 키워드 순위 검색")
        self.gui_event_pending_dismiss()

    def keywordSearch(self):
        current = self.keywordAndBlog.dequeue()
        target_url = current[0]
        current_keyword = current[1]
        self.search_ui_refresh(self.count.count, current_keyword, target_url)

        if target_url == "":
            # 24.02.08 : URL 미제공 시 처리 기능 추가 (미처리 시 공백 표기)
            current[2] = ""
            self.keywordAndBlog.add_finish_job(current)
            return

        self.search.init_control(current_keyword)
        rank = self.rankfind(target_url, current_keyword)
        current[2] = rank
        if not self.search.is_enlu_query:
            current[2] = (str(rank) + " (확인 필요)")
        self.keywordAndBlog.add_finish_job(current)

    # 23.06.28 : rank is one
    def rankfind(self, target_url, target_keyword):
        self.search.clear_url()
        # rank = list()
        rank = 0
        while True:
            self.search.set_url(target_keyword)
            tmp_rank, ret = self.find_rank(target_url)
            if ret == True:
                rank += tmp_rank
                break
            if self.search.isEnded == True and self.search.nextSearchStatus != searchControl.UNCHANGED:
                rank = -1
                break
            else:
                self.search.search_counting()
                rank += tmp_rank
        #rank = list(set(rank))
        # 23.06.29 : 순위 출력 제한 부분 추가
        if self.rankLimits == 0 or rank <= self.rankLimits:
            return rank
        else:
            return -1

    # 검색후 url을 찾습니다.
    def find_rank(self, target_url):
        # resource = requests.get(self.search.url, searchControl.HEADER)
        resource = Control.get_request_from_url(self.search.url)
        if resource is None:
            self.addloglist("인터넷 접속에 실패했습니다. 다음으로 진행합니다.")
            self.search.isEnded = True
            self.search.nextSearchStatus = searchControl.NONEXTURL
            return -1, False
        html_bs = BeautifulSoup(resource.text, 'html.parser')
        self.update_max_count(html_bs)
        # 23.06.28 : target_url => url
        area = html_bs.find_all('li')
        finded = []
        for href in area:
            try:
                # 23.11.07 : view탭 업데이트로 인한 로직 변경
                # view_wrap->detail_box->title_area
                tmp_str = href.contents[1].contents[2].contents[1].contents[1]['href']
                # 24.02.08 : enlu_query가 없는 검색어에 대한 처리 필요
                finded.append(tmp_str[2:len(tmp_str) - 2])
            except:
                # Not wanted information
                pass
        # area = html_bs.find_all('a', {'class': '\\\"sub_txt'})
        # finded = [tag.text for tag in area]
        # rank = self.url_blog_name_compare(target_url, finded)
        rank, ret = self.url_link_exectly_compare(target_url, finded)
        return rank, ret

    def update_max_count(self, html_bs):
        # 24.02.04 : view -> 블로그 탭으로 변경됨
        # 24.02.08 : enlu_query가 없을때의 처리 추가 필요
        # if not self.search.is_enlu_query:
        #     self.search.nextSearchStatus = searchControl.NONEXTURL
        #     return

        next_url = dict(eval("{" + html_bs.text[html_bs.text.find("nextUrl") - 1:len(html_bs.text) - 3] + "}"))[
            "nextUrl"]
        if next_url == "":
            self.search.nextSearchStatus = searchControl.NONEXTURL
        else:
            self.search.nextSearchStatus = searchControl.AVALIABLEURL

        # if self.search.nextSearchStatus == searchControl.UNCHANGED:
        #     try:
        #         self.search.nextSearchStatus = int(html_bs.text[13:16])  # total 갯수 확인
        #     except:
        #         try:
        #             self.search.nextSearchStatus = int(html_bs.text[13:15])  # total 2자리
        #         except:
        #             self.search.nextSearchStatus = int(html_bs.text[13])  # total 1자리

    def url_blog_name_compare(self, target, names: list):
        rank = list()
        for rank_idx in range(len(names)):
            if target == names[rank_idx]:
                current_rank = rank_idx + self.search.searchCurrentCount
                if self.rankLimits == 0 or current_rank <= self.rankLimits:
                    rank.append(current_rank)
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

    # url 대조 : url이 완전 일치
    def url_link_exectly_compare(self, target, urls):
        rank = 1
        for url in urls:
            if url == target:
                return rank, True
            rank += 1
        return rank, False

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
            self.error_add()
            self.error_emit.emit('순위 결과를 쓰는 도중 문제가 발생했습니다.')
            return
        self.addloglist('모든 작업이 완료되었습니다.')

    ## not used. (예전에 사용된 메서드)
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
                if not rank:
                    rank = [-1]
                before_keyword = self.preprocess_sentence_kr(before_keyword)
                string = before_keyword + '\t' + self.ranklist_to_string(rank) + '\n'
                file.write(string)
                # 23.06.24 : excel file write (rank)
                # warning : need change value.
                if not self.excel.write_rank(before_keyword, self.ranklist_to_string(rank)):
                    raise IOError
                self.add_result_item_to_table_notcompany(before_keyword, blog_name, rank)
                before_keyword = keyword
                rank = list()
            for _rank in t[2]:
                if _rank > 0:
                    rank.append(_rank)

    def print_in_excel(self):
        self.clearTable.emit()
        self.rowcnt = 0
        try:
            for t in self.keywordAndBlog.get_finish_job_list():
                url = t[0]
                keyword = t[1]
                rank = t[2]
                # 23.06.24 : excel file write (rank))
                if not self.excel.write_rank(rank):
                    raise IOError
                self.add_result_item_to_table_notcompany(keyword, url, rank)
            if not self.excel.save_excel_file():
                raise IOError
        except Exception as e:
            self.error_add()
            self.error_emit.emit('순위 결과를 쓰는 도중 문제가 발생했습니다.')
            return
        self.addloglist('모든 작업이 완료되었습니다.')
