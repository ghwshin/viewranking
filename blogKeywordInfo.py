class blogKeywordInfo:
    def __init__(self):
        self.blogLinkList = dict()
        self.companyList = []

    def add_company(self, company):
        self.companyList.append(company)

    def add_link(self, company, bid, keyword):
        try:
            self.blogLinkList[company].append([bid, keyword, 0])
        except:
            self.blogLinkList[company] = list()
            self.blogLinkList[company].append([bid, keyword, 0])

    def current_company_link_number(self, company):
        return len(self.blogLinkList[company])

    def company_list_size(self):
        return len(self.companyList)

    def dequeue(self):
        # try - catch 필요
        del self.companyList[0]

    def clear(self):
        self.blogLinkList.clear()
        self.companyList.clear()
