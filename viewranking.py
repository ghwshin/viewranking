from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
import traceback, sys, os
from UAC import UAC
from loginui import LoginUI
from main_engine import main_engine
from updateui import updateUI
import logo_rc

form_class = uic.loadUiType('ranking.ui')[0]


# excepthook을 통해서 catch 못한 오류 찾아냄
def trap_exc_during_debug(*args):
    print(args)
    with open('./debug.txt', 'w', encoding='utf8') as f:
        f.write(str(traceback.format_exception(*args)))
        f.flush()
    sys.exit(666)


sys.excepthook = trap_exc_during_debug


class MainUi(QWidget, form_class):
    def __init__(self):
        super().__init__()

        # ui loading
        self.setupUi(self)
        # thread 선언
        self.th = main_engine()

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
            # self.readPublishList()
            self.read_keyword_blog_name()
        except ValueError:
            self.logList.addItem('아이디 및 키워드 읽기에 실패했습니다. 파일을 초기화해주세요.')
        except Exception as e:
            self.logList.addItem(str(e))
            self.logList.addItem('아이디 및 키워드 읽기에 실패했습니다. 파일을 초기화해주세요.')

    def read_keyword_blog_name(self):
        self.keyw = list()
        self.blog_names = list()
        try:
            with open('./키워드.txt', 'rt', encoding='utf8') as f:
                self.keyw = f.read().split('\n')
        except Exception as e:
            # encoding 문제시
            with open('./키워드.txt', 'rt') as f:
                self.keyw = f.read().split('\n')
        try:
            with open('블로그이름.txt', 'rt', encoding='utf8') as f:
                self.blog_names = f.read().split('\n')
        except Exception as e:
            with open('블로그이름.txt', 'rt') as f:
                self.blog_names = f.read().split('\n')

        if self.keyw == [] or self.blog_names == []:
            raise ValueError

        for first in self.keyw:
            for second in self.blog_names:
                self.th.keywordAndBlog.add_link(second, first)


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
