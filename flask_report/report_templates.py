#-*- coding:utf-8 -*-
from geraldo import Report, ReportBand, ObjectValue, SystemField, BAND_WIDTH, Label, Line, FIELD_ACTION_COUNT, \
    FIELD_ACTION_SUM, FIELD_ACTION_AVG
from reportlab.lib.colors import navy
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import cm
from reportlab.pdfbase.ttfonts import TTFError
from flask.ext.babel import _


def get_func(index):
    return lambda v: v[index]


class BandDetail(ReportBand):
    height = 1 * cm

    def __init__(self, **kwargs):
        def get_elements(columns, dic):
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
                                     style={'fontName': 'hei', 'fontSize': 14, 'alignment': TA_CENTER,
                                            'textColor': navy})] + get_labels(kwargs.pop("columns", []),
                                                                              {"style": style} if style else {})


class BandSummary(ReportBand):
    height = 0.7 * cm
    borders = {'all': True}

    def __init__(self, **kwargs):
        def get_columns(columns, action=FIELD_ACTION_SUM, display_str="sum is %s"):
            return [ReportBand(height=0.6 * cm, elements=[
                Label(text=c.get("name", " "), top=0.1 * cm, left=0, style={'fontName': 'hei', 'fontSize': 14}),
                ObjectValue(attribute_name='', top=0.1 * cm,
                            left=3 * cm,
                            action=action,
                            style={'fontName': 'hei', 'fontSize': 12},
                            get_value=get_func(c.get("idx", 0)),
                            display_format=display_str)]) for c in
                    columns]

        self.elements = [Label(text=_("That's all"), top=0.1 * cm, left=0),
                         ObjectValue(attribute_name='name', top=0.1 * cm, left=3 * cm, action=FIELD_ACTION_COUNT,
                                     display_format='%s records found')]
        self.child_bands = get_columns(kwargs.pop("sum_columns", []), FIELD_ACTION_SUM) + \
            get_columns(kwargs.pop("avg_columns", []), FIELD_ACTION_AVG, "avg is %s")


class BaseReport(Report):
    title = "report"
    author = "test"
    margin_left = 2 * cm
    margin_top = 0.5 * cm
    margin_right = 0.5 * cm
    margin_bottom = 0.5 * cm


    def __init__(self, columns, queryset, report_name=None, **kwargs):
        super(BaseReport, self).__init__(queryset)
        self.band_detail = BandDetail(columns=columns)
        if report_name:
            self.title = report_name


class CSVReport(BaseReport):
    """

    """


class PDFReport(BaseReport):
    """
    PDF需要特定的字体才能展示中文
    """

    def __init__(self, columns, queryset, report_name=None, sum_columns=None, avg_columns=None):
        super(PDFReport, self).__init__(columns, queryset, report_name)
        self.band_detail = BandDetail(columns=columns, style={'fontName': 'hei', 'fontSize': 12})
        self.register_font()
        self.band_page_header = BandHeader(columns=columns, style={'fontName': 'hei', 'fontSize': 12})
        self.band_summary = BandSummary(sum_columns=sum_columns or [], avg_columns=avg_columns or [])

    def register_font(self):
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            pdfmetrics.registerFont(TTFont('hei', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'))
        except TTFError:
            import os
            import os.path

            try:
                pdfmetrics.registerFont(
                    TTFont('hei', os.path.join(os.path.dirname(os.path.abspath(__file__)), r"fonts\simhei.ttf")))
            except TTFError:
                raise


class TxtReport(BaseReport):
    """

    """
