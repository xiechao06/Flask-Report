# -*- coding: UTF-8 -*-
import os
from flask import render_template
from flask.ext.report.wrappers import ReportWrapper


class FlaskReport(object):
    def __init__(self, db, model_map, app, blueprint=None):
        from flask.ext.report import models

        models.setup_models(db)
        self.db = db
        host = blueprint or app
        self.conf_dir = app.config.get("REPORT_DIR", "report_conf")
        self.report_dir = os.path.join(self.conf_dir, "reports")
        self.data_set_dir = os.path.join(self.conf_dir, "data_sets")
        self.model_map = model_map
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
        if not os.path.exists(self.data_set_dir):
            os.makedirs(self.data_set_dir)

        host.route("/report-list")(self.report_list)
        host.route("/report/<int:id_>")(self.report)
        host.route("/report_csv/<int:id_>")(self.report_csv)
        host.route("/report_pdf/<int:id_>")(self.report_pdf)
        host.route("/report_txt/<int:id_>")(self.report_txt)

        from flask import Blueprint
        # register it for using the templates of data browser
        self.blueprint = Blueprint("report____", __name__,
                                   static_folder="static",
                                   template_folder="templates")
        app.register_blueprint(self.blueprint, url_prefix="/__report__")


    def report_list(self):
        return "this is report list"

    def report(self, id_):
        from flask.ext.report.models import Report

        report = Report.query.get_or_404(id_)
        report_wrapper = ReportWrapper(self, report)
        html_report = report_wrapper.html_template.render(data=report_wrapper.data, columns=report_wrapper.columns)
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.formatters import HtmlFormatter

        code = report_wrapper.read_literal_filter_condition()
        customized_filter_condition = highlight(code, PythonLexer(), HtmlFormatter())
        return render_template("report____/report.html", report=report, html_report=html_report,
                               customized_filter_condition=customized_filter_condition)

    def _get_report(self, id_, ReportClass):
        from flask.ext.report.reports import BaseReport
        assert issubclass(ReportClass, BaseReport)
        from flask.ext.report.models import Report

        data = Report.query.get_or_404(id_)
        wrapper = ReportWrapper(self, data)

        report = ReportClass(queryset=wrapper.data, columns=wrapper.columns)
        return report

    def _get_report_value(self, id_, ReportClass, ReportGenerator, first_row_with_column_names=False):
        from flask.ext.report.reports import BaseReport
        assert issubclass(ReportClass, BaseReport)

        from geraldo.generators import base
        assert issubclass(ReportGenerator, base.ReportGenerator)
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        return_fileobj = StringIO()
        from flask.ext.report.writer import UnicodeWriter

        report = self._get_report(id_, ReportClass)

        report.generate_by(ReportGenerator, filename=return_fileobj, writer=UnicodeWriter(return_fileobj),
                           first_row_with_column_names=first_row_with_column_names)
        return return_fileobj

    def report_csv(self, id_):
        # TODO unimplemented
        from flask.ext.report.reports import CSVReport
        from geraldo.generators import CSVGenerator
        return_fileobj = self._get_report_value(id_, CSVReport, CSVGenerator, True)
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="text/csv")
        response.headers["Content-disposition"] = "attachment; filename={}.csv".format(str(id_))
        return response

    def report_pdf(self, id_):
        # TODO unimplemented
        from flask.ext.report.reports import PDFReport
        from geraldo.generators import PDFGenerator
        return_fileobj = self._get_report_value(id_, PDFReport, PDFGenerator, True)
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="application/pdf")
        response.headers["Content-disposition"] = "attachment; filename={}.pdf".format(str(id_))
        return response

    def report_txt(self, id_):
        # TODO unimplemented
        from flask.ext.report.reports import TxtReport
        from geraldo.generators import TextGenerator
        return_fileobj = self._get_report_value(id_, TxtReport, TextGenerator, True)
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="text/plan")
        response.headers["Content-disposition"] = "attachment; filename={}.txt".format(str(id_))
        return response
