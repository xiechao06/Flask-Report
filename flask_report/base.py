# -*- coding: UTF-8 -*-
import os
import json
from flask import render_template, abort, request, url_for, redirect
from flask.ext.report.report import Report
from flask.ext.report.data_set import DataSet
from flask.ext.report.utils import get_column_operated


class FlaskReport(object):
    def __init__(self, db, model_map, app, blueprint=None, extra_params=None, table_label_map=None):
        self.db = db
        self.app = app
        host = blueprint or app
        self.conf_dir = app.config.get("REPORT_DIR", "report_conf")
        self.report_dir = os.path.join(self.conf_dir, "reports")
        self.data_set_dir = os.path.join(self.conf_dir, "data_sets")
        self.model_map = model_map # model name -> model
        self.table_label_map = table_label_map or {}
        self.table_map = dict((model.__tablename__, model) for model in model_map.values()) # table name -> model
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
        if not os.path.exists(self.data_set_dir):
            os.makedirs(self.data_set_dir)

        host.route("/report-list/")(self.report_list)
        host.route("/report/", methods=["GET", "POST"])(self.report)
        host.route("/report/<int:id_>")(self.report)
        host.route("/report_csv/<int:id_>")(self.report_csv)
        host.route("/report_pdf/<int:id_>")(self.report_pdf)
        host.route("/report_txt/<int:id_>")(self.report_txt)
        host.route("/drill-down-detail/<int:report_id>/<int:col_id>")(self.drill_down_detail)

        host.route("/data-sets/")(self.data_set_list)
        host.route("/data-set/<int:id_>")(self.data_set)

        from flask import Blueprint
        # register it for using the templates of data browser
        self.blueprint = Blueprint("report____", __name__,
                                   static_folder="static",
                                   template_folder="templates")
        app.register_blueprint(self.blueprint, url_prefix="/__report__")
        self.extra_params = extra_params or {'report': {}, 'report_list': {}}

    def data_set_list(self):
        data_sets = [DataSet(self, int(dir_name)) for dir_name in os.listdir(self.data_set_dir) if
                     dir_name.isdigit() and dir_name != '0']
        params = dict(data_sets=data_sets)
        extra_params = self.extra_params.get("data_sets")
        if extra_params:
            params.update(extra_params)
        return render_template("report____/data-sets.html", **params)

    def data_set(self, id_):
        data_set = DataSet(self, id_)
        data = []
        current_filters = []
        yaml = None
        if request.args.get("filters"):
            data = json.loads(request.args.get("filters"))
            current_filters = data_set.get_current_filters(data)
            yaml = data_set.parse_filters(data)
            data = data_set.get_query(data).all()
        html = data_set.html_template.render(columns=data_set.columns, data=data)
        params = dict(data_set=data_set, html=html, filters=data_set.filters, current_filters=current_filters,
                      filters_yaml=yaml)
        return render_template("report____/data-set.html", **params)

    def report_list(self):
        # directory 0 is reserved for special purpose
        reports = [Report(self, int(dir_name)) for dir_name in os.listdir(self.report_dir) if
                   dir_name.isdigit() and dir_name != '0']
        params = dict(reports=reports)
        extra_params = self.extra_params.get('report_list')
        if extra_params:
            params.update(extra_params)
        return render_template('report____/report-list.html', **params)

    def report(self, id_=None):
        if id_ is not None:
            report = Report(self, id_)
            html_report = report.html_template.render(data=report.data, columns=report.columns, report=report)
            from pygments import highlight
            from pygments.lexers import PythonLexer
            from pygments.formatters import HtmlFormatter

            code = report.read_literal_filter_condition()
            params = dict(report=report, html_report=html_report)
            if code is not None:
                customized_filter_condition = highlight(code, PythonLexer(), HtmlFormatter())
                params[customized_filter_condition] = customized_filter_condition
            extra_params = self.extra_params.get("report")
            if extra_params:
                params.update(extra_params)
            return render_template("report____/report.html", **params)
        else:
            id_ = max([int(dir_name) for dir_name in os.listdir(self.report_dir) if
                       dir_name.isdigit() and dir_name != '0']) + 1
            new_dir = os.path.join(self.report_dir, str(id_))
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)
            self._write(os.path.join(new_dir, "meta.yaml"), request.form)
            return redirect(url_for(".report", id_=id_, _method="GET"))

    def _write(self, file_name, form):
        import yaml
        dict_ = {"name": form["report_name"], "description": form["report_desc"],
                 "data_set_id": form.get("data_set_id", type=int),
                 "filters": yaml.load(form["report_filters"]), "columns": form.getlist("report_columns", type=int)}
        if form.get("report_order_by"):
            dict_["order_by"] = form["report_order_by"]
        dict_["creator"] = form["report_creator"]
        import datetime
        dict_["create_time"] = datetime.datetime.now()
        with file(file_name, "w") as f:
            yaml.safe_dump(dict_, allow_unicode=True, stream=f)

    def _get_report(self, id_, ReportClass):
        from flask.ext.report.report_templates import BaseReport

        assert issubclass(ReportClass, BaseReport)
        data = Report(self, id_)
        if not data.data:
            raise ValueError
        report = ReportClass(queryset=data.data, columns=data.columns, report_name=data.name,
                             sum_columns=data.sum_columns, avg_columns=data.avg_columns)
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


    def get_model_label(self, table):
        return self.table_label_map.get(table.name) or self.table_map[table.name].__name__

    def drill_down_detail(self, report_id, col_id):
        filters = request.args
        report = Report(self, report_id)
        col = report.data_set.columns[col_id]['expr']
        col = get_column_operated(getattr(col, 'element', col))
        model_name = self.get_model_label(col.table)
        return report.get_drill_down_detail_template(col_id).render(items=report.get_drill_down_detail_query(col_id, **filters).all(), 
                                                                    key=col.key, 
                                                                    model_name=model_name, 
                                                                    report=report)
