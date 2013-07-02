#-*- coding:utf-8 -*-
from geraldo import Report, ReportBand, ObjectValue
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


class BaseReport(Report):
    title = "test"
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

    def register_font(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(TTFont('hei', 'simhei.TTF'))
        except:
            raise


class TxtReport(BaseReport):
    """

    """