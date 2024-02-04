from blogKeywordInfo import blogKeywordInfo
from queue import SimpleQueue

"""
    23.06.28
    blogKeywordUrls 구조
    list[3] = {urls, keyword, rank(list)}
"""


class blogKeywordUrls(blogKeywordInfo):
    def __init__(self):
        super().__init__()

    def add_link(self, urls, keyword):
        if self.blogLinkList == None:
            self.blogLinkList = SimpleQueue()
            self.blogLinkList.put([urls, keyword, list()])
        else:
            self.blogLinkList.put([urls, keyword, list()])
