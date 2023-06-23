import openpyxl


class ExcelControl:
    def __init__(self, wb_file_name):
        self.workbook = self.open_workbook(wb_file_name)
        self.excel_file_name = wb_file_name
        self.row_keyword_pair = {}

    # open workbook
    def open_workbook(self, file_name):
        try:
            wb = openpyxl.load_workbook(file_name)
        except FileNotFoundError:
            print(f"{file_name} 파일을 찾지 못했음")
            return None
        return wb

    def control_status_check(self):
        if self.workbook == None:
            return False
        else:
            return True

    def access_point_check(self, row, column):
        if row <= 1 or column <= 1:
            return False
        else:
            return True

    # data example : [["data", 2], ["data2", 3]]
    # (row, column) ~ (row + data row len, column + data column len)
    def _write_excel(self, data, row, column):
        ws = self.workbook.active
        if not self.control_status_check():
            return False
        if not self.access_point_check(row, column):
            return False
        for i, row_data in enumerate(data):
            for j, cell_data in enumerate(row_data):
                ws.cell(row=row + i, column=column + j, value=cell_data)
        try:
            self.workbook.save(self.excel_file_name)
        except Exception as e:
            print(e)
            return False
        return True

    def _read_excel(self, row, column):
        ws = self.workbook.active
        if not self.control_status_check():
            return None
        if not self.access_point_check(row, column):
            return None
        try:
            cell_value = ws.cell(row=row, column=column).value
        except Exception as e:
            print(e)
            return None
        return cell_value

    def read_keyword(self):
        row_idx = 2
        col_idx = 2
        keywords = []
        while True:
            ret = self._read_excel(row_idx, col_idx)
            if ret == None or ret == "":
                break
            # self.row_keyword_pair.append([row_idx, ret])
            self.row_keyword_pair[ret] = row_idx
            keywords.append(ret)
            row_idx += 1

        return keywords

    def write_rank(self, keyword, rank, rank_col=4):
        row = self.row_keyword_pair[keyword]
        if not self.access_point_check(row, rank_col):
            return False
        return self._write_excel([[rank]], row, rank_col)


if __name__ == '__main__':
    ec = ExcelControl("rank_check.xlsx")
    if ec._write_excel([[3]], 2, 4):
        print("success")
    else:
        print("failed")
    ret = ec._read_excel(2, 3)
    print(ret)
    ret = ec._read_excel(2, 4)
    print(ret)
