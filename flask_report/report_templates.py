#-*- coding:utf-8 -*-
from geraldo import Report, ReportBand, ObjectValue, SystemField, BAND_WIDTH, Label, Line
from reportlab.lib.colors import navy
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm


class BandDetail(ReportBand):
    height = 1 * cm

    def __init__(self, **kwargs):
        def get_elements(columns, dic):
            def get_func(index):
                return lambda v: v[index]


            return [ObjectValue(name=c.get("name", str(c.get('idx', 0))), attribute_name=c,
                                get_value=get_func(c.get("idx", 0)), left=0 + c.get("idx", 0) * 3 * cm, **dic) for c in
                    columns]

        style = kwargs.get("style")
        self.elements = get_elements(kwargs.pop("columns", []), {"style": style} if style else {})
        super(BandDetail, self).__init__(**kwargs)


class BandHeader(ReportBand):
    height = 1.3 * cm
    borders = {'bottom': Line(stroke_color=navy)}

    def __init__(self, **kwargs):
        style = kwargs.get("style")

        def get_labels(columns, dic):
            return [Label(text=c.get("name", " "), top=0.8 * cm, left=0 + c.get("idx", 0) * 3 * cm, **dic) for c in
                    columns]

        self.elements = [SystemField(expression='%(report_title)s', top=0.1 * cm, left=0, width=BAND_WIDTH,
                                     style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER,
                                            'textColor': navy})] + get_labels(kwargs.pop("columns", []),
                                                                              {"style": style} if style else {})


class BaseReport(Report):
    title = "report"
    author = "test"
    margin_left = 2 * cm
    margin_top = 0.5 * cm
    margin_right = 0.5 * cm
    margin_bottom = 0.5 * cm


    def __init__(self, columns, queryset):
        super(BaseReport, self).__init__(queryset)
        self.band_detail = BandDetail(columns=columns)


class CSVReport(BaseReport):
    """

    """


class PDFReport(BaseReport):
    """
    PDF需要特定的字体才能展示中文
    """

    def __init__(self, columns, queryset):
        super(BaseReport, self).__init__(queryset)
        self.band_detail = BandDetail(columns=columns, style={'fontName': 'hei', 'fontSize': 12})
        self.register_font()
        self.band_page_header = BandHeader(columns=columns, style={'fontName': 'hei', 'fontSize': 12})

    def register_font(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(TTFont('hei', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'))
        except:
            raise


class TxtReport(BaseReport):
    """

    """
