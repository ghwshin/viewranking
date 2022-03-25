from PyQt5.QtWidgets import *
import ctypes,sys

class UAC(QWidget):
    def uacUI(self):
        self.setGeometry(630, 350, 600, 400)
        if ctypes.windll.shell32.IsUserAnAdmin():
            pass
        else:
            reply = QMessageBox.about(self, '에러', '관리자 권한으로 실행해주십시오.')
            sys.exit()