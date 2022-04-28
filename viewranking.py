from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import traceback, sys, os
from UAC import UAC
from loginui import LoginUI
from main_thread import main_thread
from updateui import updateUI

form_class = uic.loadUiType('ranking.ui')[0]


# excepthook을 통해서 catch 못한 오류 찾아냄
def trap_exc_during_debug(*args):
    print(args)
    with open('./debug.txt', 'w', encoding='utf8') as f:
        f.write(str((traceback.format_exception)(*args)))
        f.flush()
    sys.exit(666)

sys.excepthook = trap_exc_during_debug


class MainUi(QWidget, form_class):
    def __init__(self):
        super().__init__()
        # 기타 클래스 인스턴스 변수

        # ui loading
        self.setupUi(self)
        # thread 선언
        self.th = main_thread()

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
            self.th.keywordAndBlog.clear()
            self.logList.clear()
            self.logList.addItem('순위 검색을 시작합니다.')
            #self.readPublishList()
            self.readKeywordID()
        except ValueError:
            self.logList.addItem('아이디 및 키워드 읽기에 실패했습니다. 파일을 초기화해주세요.')
        except Exception as e:
            self.logList.addItem(str(e))
            self.logList.addItem('아이디 및 키워드 읽기에 실패했습니다. 파일을 초기화해주세요.')


    def readKeywordID(self):
        self.keyw = list()
        self.ids = list()
        try:
            with open('./키워드.txt', 'rt', encoding='utf8') as f:
                self.keyw = f.read().split('\n')
        except Exception as e:
            # encoding 문제시
            with open('./키워드.txt', 'rt') as f:
                self.keyw = f.read().split('\n')
        try:
            with open('./아이디.txt', 'rt', encoding='utf8') as f:
                self.ids = f.read().split('\n')
        except Exception as e:
            with open('./아이디.txt', 'rt') as f:
                self.ids = f.read().split('\n')

        if self.keyw == [] or self.ids == []:
            raise ValueError

        for first in self.keyw:
            for second in self.ids:
                self.th.keywordAndBlog.add_link(second, first)


    '''
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
    '''


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
