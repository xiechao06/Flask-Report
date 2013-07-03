# -*- coding: UTF-8 -*-
import os
from flask import render_template, abort
from flask.ext.report.report import Report


class FlaskReport(object):
    def __init__(self, db, model_map, app, blueprint=None, extra_params=None):
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

        host.route("/report-list/")(self.report_list)
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
        self.extra_params = extra_params or {}


    def report_list(self):
        # directory 0 is reserved for special purpose
        reports = [Report(self, int(dir_name)) for dir_name in os.listdir(self.report_dir) if
                   dir_name.isdigit() and dir_name != '0']
        return render_template('report____/report-list.html', reports=reports, **self.extra_params.get('report_list'))

    def report(self, id_):
        report = Report(self, id_)
        html_report = report.html_template.render(data=report.data, columns=report.columns)
        from pygments import highlight
        from pygments.lexers import PythonLexer
        from pygments.formatters import HtmlFormatter

        code = report.read_literal_filter_condition()
        customized_filter_condition = highlight(code, PythonLexer(), HtmlFormatter())
        return render_template("report____/report.html", report=report, html_report=html_report,
                               customized_filter_condition=customized_filter_condition, **self.extra_params.get('report'))

    def _get_report(self, id_, ReportClass):
        from flask.ext.report.report_templates import BaseReport

        assert issubclass(ReportClass, BaseReport)
        data = Report(self, id_)
        if not data.data:
            raise ValueError
        report = ReportClass(queryset=data.data, columns=data.columns)
        return report

    def _get_report_value(self, id_, ReportClass, ReportGenerator, first_row_with_column_names=False):
        from flask.ext.report.report_templates import BaseReport

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

    def _get_report_class(self, id_, default=None):
        if default is None:
            raise ValueError
        filter_def_file = os.path.join(self.report_dir, str(id_), "report_templates.py")
        if not os.path.exists(filter_def_file):
            filter_def_file = os.path.join(self.report_dir, "0", "report_templates.py")
        if os.path.exists(filter_def_file):
            from import_file import import_file

            lib = import_file(filter_def_file)
            return getattr(lib, default.__name__, None) or default

    def report_csv(self, id_):
        # TODO unimplemented
        from geraldo.generators import CSVGenerator
        from flask.ext.report.report_templates import CSVReport

        try:
            return_fileobj = self._get_report_value(id_, self._get_report_class(id_, CSVReport), CSVGenerator, True)
        except ValueError:
            return render_template("report____/error.html", error=u"没有该报告", message=u"无法导出空报告"), 403
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="text/csv")
        response.headers["Content-disposition"] = "attachment; filename={}.csv".format(str(id_))
        return response

    def report_pdf(self, id_):
        from flask.ext.report.report_templates import PDFReport
        from geraldo.generators import PDFGenerator

        try:
            return_fileobj = self._get_report_value(id_, self._get_report_class(id_, PDFReport), PDFGenerator, True)
        except ValueError:
            return render_template("report____/error.html", error=u"没有该报告", message=u"无法导出空报告"), 403
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="application/pdf")
        response.headers["Content-disposition"] = "attachment; filename={}.pdf".format(str(id_))
        return response

    def report_txt(self, id_):
        from flask.ext.report.report_templates import TxtReport

        from geraldo.generators import TextGenerator

        try:
            return_fileobj = self._get_report_value(id_, self._get_report_class(id_, TxtReport), TextGenerator, True)
        except ValueError:
            return render_template("report____/error.html", error=u"没有该报告", message=u"无法导出空报告"), 403
        from flask import Response

        response = Response(return_fileobj.getvalue(), mimetype="text/plan")
        response.headers["Content-disposition"] = "attachment; filename={}.txt".format(str(id_))
        return response
