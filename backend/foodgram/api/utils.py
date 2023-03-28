from fpdf import FPDF


class CustomPDF(FPDF):

    def __init__(self, font_dir):
        super().__init__()
        self.encoding = 'utf-8'
        self.font_dir = font_dir
        self.add_font(
            'DejaVu',
            '',
            f'{self.font_dir}/DejaVuSansCondensed.ttf',
            uni=True,
        )
        self.set_font('DejaVu', '', 14)

    def header(self):
        self.set_font("DejaVu", "", 15)
        self.cell(80)
        self.cell(30, 10, 'Title', 1, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')

    def chapter_title(self, num, label):

        self.set_font("DejaVu", '', 12)
        self.cell(0, 10, f'Chapter {num} : {label}', 0, 1)

    def chapter_body(self, ingredient_dict):

        self.set_font("DejaVu", size=12)
        for name, details in ingredient_dict.items():
            self.cell(
                0,
                10,
                f"{name} - {details['amount']} {details['unit']}",
                ln=1,
            )

    def print_chapter(self, num, title, ingredient_dict):

        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(ingredient_dict)
