from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5 import uic
from PyQt5 import QtTest
from bs4 import BeautifulSoup
import requests, boto3, win32api, win32con
import traceback, sys, os, datetime
from blogKeywordInfo import blogKeywordInfo
from Control import *
from UAC import UAC
import logo_rc

form_class = uic.loadUiType('ranking.ui')[0]
service_name = 's3'
endpoint_url = 'https://kr.object.ncloudstorage.com'
region_name = 'kr-standard'
access_key = 'JS96LdRZxwUaJ7hlS8oX'
secret_key = 'dBofyAEvH84Mm6ESChoojJcWUkkitu7VFVUMY9Ii'
version = '1.22'


# excepthook을 통해서 catch 못한 오류 찾아냄
def trap_exc_during_debug(*args):
    print(args)
    with open('./debug.txt', 'w', encoding='utf8') as f:
        f.write(str((traceback.format_exception)(*args)))
        f.flush()
    sys.exit(666)


sys.excepthook = trap_exc_during_debug


class multi_thread(QThread):
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
    """

    def __init__(self):
        QThread.__init__(self)
        self.today = datetime.datetime.today().strftime('%Y-%m-%d')
        self.companyAndBlog = blogKeywordInfo()
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
        self.count.setCountMax(len(self.companyAndBlog.companyList))
        self.progressClear()
        while self.companyAndBlog.company_list_size() != 0:
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
        currentCompany = self.companyAndBlog.companyList[0]
        self.addloglist(currentCompany + " 회사 발행 순위 검색 시작")
        try:
            linkrange = self.companyAndBlog.current_company_link_number(currentCompany)
        except:
            self.error_emit.emit('파일 중 빈 파일이나 깨진 파일이 발견되었습니다. 다시 넣어주세요.')
            raise FileNotFoundError
        for i in range(linkrange):
            self.gui_event_pending_dismiss()
            targetLink = self.companyAndBlog.blogLinkList[currentCompany][i][0]
            targetKeyword = self.companyAndBlog.blogLinkList[currentCompany][i][1]
            self.search_ui_refresh(i, linkrange, targetKeyword)
            self.search.init_control()
            # TODO : 아래 줄부터 랭크 반복문 설정
            rank = self.rankfind(targetLink, targetKeyword)
            # 랭크 설정!
            self.companyAndBlog.blogLinkList[currentCompany][i][2] = rank
        self.companyAndBlog.dequeue()

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
        rank = self.url_link_compare(targetLink, find_url)
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

    def after_serach(self):
        self.clearTable.emit()
        self.rowcnt = 0
        try:
            total_txt = './결과/통합순위_' + self.today + '.txt'
            with open(total_txt, 'w') as f:
                for company in self.companyAndBlog.blogLinkList.keys():
                    self.print_result(company, f)
        except:
            self.error_emit.emit('순위 결과를 쓰는 도중 문제가 발생했습니다.')
            return
        self.addloglist('모든 작업이 완료되었습니다.')

    def print_result(self, company, file):
        company_txt = './결과/' + company + '_' + self.today + '.txt'
        with open(company_txt, 'w') as file_company:
            for i in range(self.companyAndBlog.current_company_link_number(company)):
                link = self.companyAndBlog.blogLinkList[company][i][0]
                keyword = self.companyAndBlog.blogLinkList[company][i][1]
                rank = self.companyAndBlog.blogLinkList[company][i][2]
                if rank == 0:
                    rank = '누락'
                string = company + '\t' + keyword + '\t' + link + '\t' + str(rank) + '\n'
                # log_string = company + '  ' + keyword + '  ' + link + '  ' + str(rank) + '  '
                file_company.write(string)
                file.write(string)
                self.add_result_item_to_table(company, keyword, rank)

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


class MainUi(QWidget, form_class):
    def __init__(self):
        super().__init__()
        # 기타 클래스 인스턴스 변수

        # ui loading
        self.setupUi(self)
        # thread 선언
        self.th = multi_thread()

        # error connect
        self.th.error_emit.connect(self.error_handler)

        # button connect
        self.startButton.clicked.connect(self.startButton_clicked)

        # signal logList(로그)
        self.th.addLog.connect(self.logList.addItem)
        self.th.afterAddLog.connect(self.logList.scrollToBottom)
        self.th.clear_value.connect(self.logList.clear)

        # signal resultTable
        self.th.setRowValue.connect(self.resultTable.setRowCount)
        self.th.clearTable.connect(self.resultTable.clearContents)
        self.th.addResult.connect(self.add_result)

        # signal progressBar
        self.th.setProgressValue.connect(self.progressBar.setValue)

        # signal label
        self.th.setKeywordRemain.connect(self.keywordRemainIndicator.setText)
        self.th.setCurrentKeyword.connect(self.currentkeywordIndicator.setText)

        # signal checkbox
        self.allCheckBox.stateChanged.connect(self.all_find_checked)

        # label repaint
        self.th.label_repaint.connect(self.labelrepaint)

    @pyqtSlot(int, int, str)
    def add_result(self, row, col, data):
        self.resultTable.setItem(row, col, QTableWidgetItem(data))

    def clear_result(self):
        self.resultTable.clearContents()

    def error_handler(self, e):
        QMessageBox.about(self, '에러', e)

    def labelrepaint(self):
        self.currentkeywordIndicator.repaint()
        self.keywordRemainIndicator.repaint()

    # 전체 검색 관련 메서드
    def all_find_checked(self):
        if self.allCheckBox.isChecked():
            self.th.search.isAllSerach = True
        else:
            self.th.search.isAllSerach = False

    # 버튼 클릭 관련 메서드
    def startButton_clicked(self):
        print('start')
        self.startWorkInit()
        self.th.start()

    # 시작 버튼을 눌렀을 때 초기화 함수
    def startWorkInit(self):
        try:
            self.th.companyAndBlog.clear()
            self.logList.clear()
            self.logList.addItem('순위 검색을 시작합니다.')
            self.readPublishList()
        except Exception as e:
            self.logList.addItem(str(e))
            self.logList.addItem('발행글 및 키워드 읽기에 실패했습니다. 파일을 초기화해주세요.')

    # 데이터 처리 메서드
    # 발행글 읽기 : 실패시 valueError
    def readPublishList(self):
        file_list = os.listdir('./발행글링크')
        if file_list == []:
            raise ValueError
        for file in file_list:
            currentCompanyName = file[:-4]
            self.th.companyAndBlog.add_company(currentCompanyName)  # 파일 이름 확장자 제외 : 회사명
            file_dir = './발행글링크/' + file
            try:
                with open(file_dir, 'rt', encoding='utf8') as f:
                    self.read_link(currentCompanyName, f)
            except IndexError as e:
                pass
            except Exception as e:  # encoding 문제 발생시
                with open(file_dir, 'rt') as f:
                    self.read_link(currentCompanyName, f)

    def read_link(self, currentCompanyName, f):
        link_and_keyword = f.read().splitlines()  # 분리
        for tmp in link_and_keyword:
            link = self.no_tap_twice(tmp)
            # 탭문자 중복 방지용입니다.
            keyword = tmp.split('\t')[0]
            # robust test : 잘못된 입력?
            self.th.companyAndBlog.add_link(currentCompanyName, link, keyword)

    def no_tap_twice(self, tmp):
        i = 1
        while True:
            link = tmp.split('\t')[i]
            if link == '' or link == '\t':
                i += 1
            else:
                break
        return link


# 아래부터는 인증파트
class updateUI(QWidget):  # update check
    def mainUI(self):
        self.setGeometry(630, 350, 600, 400)
        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
        bucket_name = 'viewranking'
        object_name = 'version.txt'
        local_file_path = './data/version.txt'
        try:
            s3.download_file(bucket_name, object_name, local_file_path)
        except Exception as e:
            QMessageBox.about(self, '에러', '버전 정보를 받아오는 데 실패했습니다.')
            sys.exit()

        with open('./data/version.txt', 'rt') as f:
            ver = f.read()
        if ver != version:
            QMessageBox.about(self, '업데이트 필요', '업데이트가 필요합니다. 프로그램을 종료합니다.')
            sys.exit()
        os.remove('./data/version.txt')


class LoginUI(QWidget):  # login part
    def mainUI(self):
        self.setGeometry(630, 350, 600, 400)
        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
        bucket_name = 'viewranking'
        id, ok = QInputDialog.getText(self, '아이디 입력', '로그인을 위한 아이디를 입력하십시오.')
        if ok:
            while True:
                object_name = id + '.txt'
                local_file_path = './acc.txt'
                try:
                    s3.download_file(bucket_name, object_name, local_file_path)
                    break
                except:
                    QMessageBox.about(self, '아이디 오류', '계정이 존재하지 않습니다.')

            try:
                with open('./acc.txt', 'rt', encoding='utf8') as f:
                    login = f.read().splitlines()
                passw, ok = QInputDialog.getText(self, '비밀번호 입력', '로그인을 위한 비밀번호를 입력하십시오.', echo=2)
                if ok:
                    if passw == login[0]:
                        try:
                            dir = 'C:\\ProgramData'
                            path = os.path.join(dir, 'logvr.ps')
                            with open(path, 'w', encoding='utf8') as f:
                                f.write(
                                    '\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n' + id + '\n' + passw)
                            win32api.SetFileAttributes(path, win32con.FILE_ATTRIBUTE_HIDDEN)
                            s3.delete_object(Bucket=bucket_name, Key=object_name)
                            os.remove('./acc.txt')
                        except:
                            re = QMessageBox.about(self, '인증 실패', '로그인 중 중대한 오류가 발생했습니다. 관리자에게 문의하십시오.')
                            os.remove('./acc.txt')
                            sys.exit()

                    else:
                        re = QMessageBox.about(self, '인증 실패', '비밀번호가 틀렸습니다. 다시 시도하십시오.')
                        os.remove('./acc.txt')
                        sys.exit()
                else:
                    os.remove('./acc.txt')
                    sys.exit()
            except:
                re = QMessageBox.about(self, '인증 실패', '로그인 초기 오류가 발생했습니다. 관리자에게 문의하십시오.')
                os.remove('./acc.txt')
                sys.exit()

        else:
            sys.exit()


if __name__ == '__main__':
    ranking_app = QApplication(sys.argv)
    uac = UAC()
    uac.uacUI()

    mainWindow = MainUi()
    loginui = LoginUI()
    updateui = updateUI()
    updateui.mainUI()

    logpath = os.path.join('C:\\ProgramData', 'logvr.ps')
    if os.path.exists(logpath):
        mainWindow.show()
        sys.exit(ranking_app.exec_())
    else:
        loginui = LoginUI()
        loginui.mainUI()
        mainWindow.show()
        sys.exit(ranking_app.exec_())
