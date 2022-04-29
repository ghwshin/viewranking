from queue import *


class blogKeywordInfo:
    """
        blogKeywordInfo 클래스 설명
        companyList : 회사 리스트
        blogLinkList : dict 구조입니다.
        22.03.25 추가
        1. 링크 -> 블로그 아이디로 교체
        2. 랭크를 list로 교체
        3. 랭크 크롤링을 다수로 변경

        22.04.01 변경
        1. 더이상 회사는 유효하지 않습니다. (삭제)
        2. blogLinkList를 list로 변경하였습니다.
        ([bid, keyword, rank])

        22.04.29 변경
        1. 데이터 구조를 변경하였습니다. (큐로 구성)
        2. 구조는 다음과 같습니다.
        list[3] = {blog_name, keyword, rank(list)}
    """

    def __init__(self):
        self.blogLinkList = SimpleQueue()
        self.finished_list = list()
        self.size = 0

    def add_link(self, blog_name, keyword):
        if self.blogLinkList == None:
            self.blogLinkList = SimpleQueue()
            self.blogLinkList.put([blog_name, keyword, list()])
        else:
            self.blogLinkList.put([blog_name, keyword, list()])

    def current_size(self):
        self.size = self.blogLinkList.qsize()
        return self.size

    def dequeue(self):
        return self.blogLinkList.get()

    def finish_list_empty(self):
        return len(self.finished_list) == 0

    def add_finish_job(self, job):
        self.finished_list.append(job)

    def get_finish_job_list(self):
        return self.finished_list

    def clear(self):
        self.blogLinkList = None
        self.finished_list = []
