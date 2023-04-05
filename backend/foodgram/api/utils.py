from fpdf import FPDF


class CustomPDF(FPDF):

    def __init__(self):
        super().__init__()
        self.add_font('DejaVu', '', 'static/fonts/DejaVuSansCondensed.ttf')

    def header(self):
        self.image('static/logo192.png', self.w / 2 - 16, 8, 33)
        self.set_font('DejaVu', '', 14)
        self.ln(40)
        self.cell(0, 10, 'Cписок покупок', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_font('DejaVu', '', 14)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 2, 'C')
        self.cell(0, 10, 'Foodgram: lkaydalov.ddns.net', 0, 0, 'C')

    def chapter_body(self, ingredient_dict):

        self.set_font('DejaVu', '', 14)
        for name, details in ingredient_dict.items():
            self.cell(
                0,
                10,
                f"{name}: {details['amount']} {details['unit']}",
                ln=1,
            )

    def print_chapter(self, ingredient_dict):

        self.add_page()
        self.set_font('DejaVu', '', 14)
        self.chapter_body(ingredient_dict)
