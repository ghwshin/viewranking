import os
import sys

import boto3
from PyQt5.QtWidgets import QWidget, QMessageBox

from service_key import service_name, endpoint_url, access_key, secret_key, version


class updateUI(QWidget):  # update check
    def mainUI(self):
        self.setGeometry(630, 350, 600, 400)
        s3 = boto3.client(service_name, endpoint_url=endpoint_url, aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
        bucket_name = 'viewranking'
        object_name = 'version2.txt'
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
