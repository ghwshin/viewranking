class blogKeywordInfo:
    def __init__(self):
        self.blogLinkList = list()
        self.firstsize = 0
        self.cur = 0

    def add_link(self, bid, keyword):
        try:
            self.blogLinkList.append([bid, keyword, 0])
        except:
            self.blogLinkList = list()
            self.blogLinkList.append([bid, keyword, 0])

    def current_list_size(self):
        return len(self.blogLinkList)

    def dequeue(self):
        # try - catch 필요
        self.cur += 1

    def clear(self):
        self.blogLinkList.clear()
