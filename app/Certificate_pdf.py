from fpdf import FPDF 
import sys
import os

cert_template_path = os.path.join(".", "app", "static", "cert", "證書模板.png")
edukai_path = os.path.join(".", "app", "static", "cert", "edukai-5.0.ttf")

class PDF(FPDF):
    def add_certificate_content(self, name, course_title, department_name, hour, year, month, day, certification_code):
        self.image(cert_template_path, 0, 0, 210, 297)  # 设置证书背景图片
        self.set_xy(100, 62)
        self.set_font('edukai', '', 20)
        STR = f"{certification_code}"
        self.cell(0, 0, STR)
        #self.set_font('kaiu', '', 36)  # 设置字体和大小
        self.set_font('edukai', '', 36)  # 设置字体和大小
        STR = f"茲證明{name}於{year}年{month}月{day}日參加{department_name}辦理「{course_title}」研習活動，研習時數總計{hour}小時，特此證明。"
        self.set_xy(16, 70)
        self.multi_cell(0, 15, STR)
        self.set_xy(18, 170)
        self.cell(0, 0, "校長")
        self.set_font('edukai', '', 24)
        self.set_xy(0, 270)
        self.cell(210, 0, f"中華民國 {year} 年 {month} 月 {day} 日", align='C')

#生成PDF证书
def generate_certificate(name, course_title, department_name, hour, year, month, day, certification_code, cert_path):
    if 1:
        pdf = PDF('P', 'mm', 'A4')
        pdf.add_font('edukai', '', edukai_path , uni=True)
        pdf.add_page()
        pdf.add_certificate_content(name, course_title, department_name, hour, year, month, day, certification_code)

        pdf.output(cert_path)
        print(f"Certificate generated: {cert_path}")
    else:
        print("No user data available for certificate generation.")


'''
if __name__ == "__main":
    if len(sys.argv) != 9:
        print("Usage: external_script.py <name> <course_title> <department_name> <hour> <year> <month> <day> <cert_path>")
        sys.exit(1)
        
print("Usage: external_script.py <name> <course_title> <department_name> <hour> <year> <month> <day> <cert_path>")
'''
name = sys.argv[1]
course_title = sys.argv[2]
department_name = sys.argv[3]
hour = sys.argv[4]
year = sys.argv[5]
month = sys.argv[6]
day = sys.argv[7]
certification_code = sys.argv[8]
cert_path = sys.argv[9]
generate_certificate(name, course_title, department_name, hour, year, month, day, certification_code, cert_path)

