# -*- coding: UTF-8 -*-
import os
import json
import types

from flask import render_template, abort, request, url_for, redirect, jsonify
from wtforms import Form, TextField, validators, IntegerField, SelectMultipleField

from flask.ext.report.report import Report, create_report
from flask.ext.report.data_set import DataSet
from flask.ext.report.utils import get_column_operated, query_to_sql
from flask.ext.babel import gettext as _
from pygments import highlight
from pygments.lexers import PythonLexer, SqlLexer
from pygments.formatters import HtmlFormatter


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
        host.route("/new-report/", methods=['POST'])(self.new_report)
        host.route("/graphs/report/<int:id_>")(self.report_graphs)
        host.route("/report/<int:id_>", methods=['GET', 'POST'])(self.report)
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
        self.extra_params = extra_params or {'report': lambda id_: {},
                                             'report_list': lambda: {}, 
                                             'data_set': lambda id_: {},
                                             'data_sets': lambda: {}}

        @app.template_filter("dpprint")
        def dict_pretty_print(value):
            if not isinstance(value, list):
                value = [value]
            s = "{"
            for val in value:
                idx = 0
                for k, v in val.items():
                    idx += 1
                    s += "%s:%s" % (k, v)
                    if idx != len(val):
                        s += ","
            s += "}"
            return s

    def try_view_report(self):
        pass

    def try_edit_data_set(self):
        pass

    def report_graphs(self, id_):
        report = Report(self, id_)
        return render_template("report____/graphs.html", url=request.args.get("url"), bar_charts=report.bar_charts,
                               name=report.name, pie_charts=report.pie_charts)

    def data_set_list(self):
        self.try_edit_data_set()
        data_sets = [DataSet(self, int(dir_name)) for dir_name in os.listdir(self.data_set_dir) if
                     dir_name.isdigit() and dir_name != '0']
        params = dict(data_sets=data_sets)
        extra_params = self.extra_params.get("data_sets")
        if extra_params:
            if isinstance(extra_params, types.FunctionType):
                extra_params = extra_params()
            params.update(extra_params)
        return render_template("report____/data-sets.html", **params)

    def data_set(self, id_):
        self.try_edit_data_set()
        data_set = DataSet(self, id_)

        SQL_html = highlight(query_to_sql(data_set.query), SqlLexer(), HtmlFormatter())
        params = dict(data_set=data_set, SQL=SQL_html)
        extra_params = self.extra_params.get('data_set')
        if extra_params:
            if isinstance(extra_params, types.FunctionType):
                extra_params = extra_params(id_)
            params.update(extra_params)
        return render_template("report____/data-set.html", **params)

    def report_list(self):
        self.try_view_report()
        # directory 0 is reserved for special purpose
        reports = [Report(self, int(dir_name)) for dir_name in os.listdir(self.report_dir) if
                   dir_name.isdigit() and dir_name != '0']
        params = dict(reports=reports)
        extra_params = self.extra_params.get('report_list')
        if extra_params:
            if isinstance(extra_params, types.FunctionType):
                extra_params = extra_params()
            params.update(extra_params)
        return render_template('report____/report-list.html', **params)

    def report(self, id_=None):
        self.try_view_report()
        if id_ is not None:
            report = Report(self, id_)

            html_report = report.html_template.render(data=report.data, columns=report.columns, report=report)

            code = report.read_literal_filter_condition()

            SQL_html = highlight(query_to_sql(report.query), SqlLexer(), HtmlFormatter())
            params = dict(report=report, html_report=html_report, SQL=SQL_html)
            if code is not None:
                customized_filter_condition = highlight(code, PythonLexer(), HtmlFormatter())
                params['customized_filter_condition'] = customized_filter_condition
            extra_params = self.extra_params.get("report")
            if extra_params:
                if isinstance(extra_params, types.FunctionType):
                    extra_params = extra_params(id_)
                params.update(extra_params)
            return render_template("report____/report.html", **params)
        else:
            if request.form.get("report") == "0":
                id_ = 0
            else:
                id_ = max([int(dir_name) for dir_name in os.listdir(self.report_dir) if
                           dir_name.isdigit() and dir_name != '0']) + 1
            new_dir = os.path.join(self.report_dir, str(id_))
            if not os.path.exists(new_dir):
                os.mkdir(new_dir)

            dict_ = dict(request.form.items())
            url = dict_.get("url")
            dict_["columns"] = request.form.getlist("columns", type=int)
            filters_data = json.loads(request.form["filters"])

            def parse_filters(filters):
                result = {}
                for current in filters:
                    if current["col"] not in result:
                        result[current["col"]] = {'operator': current["op"], 'value': current["val"]}
                    else:
                        val = result[current["col"]]
                        if not isinstance(val, list):
                            val = [val]
                        val.append({'operator': current["op"], 'value': current["val"]})
                        result[current["col"]] = val
                return result

            dict_["filters"] = parse_filters(filters_data)
            self._write_report(new_dir, **dict_)
            return redirect(url_for(".report", id_=id_, _method="GET", url=url))

    def _write_report(self, to_dir, **kwargs):
        import yaml

        kwargs.setdefault("name", "temp")
        kwargs.setdefault("description", "temp")
        kwargs.setdefault("data_set_id", 0)
        import datetime

        kwargs["create_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with file(os.path.join(to_dir, "meta.yaml"), "w") as f:
            yaml.safe_dump(kwargs, allow_unicode=True, stream=f)

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
        items=report.get_drill_down_detail(col_id, **filters)
        return report.get_drill_down_detail_template(col_id).render(items=items,
                                                                    key=col.key, 
                                                                    model_name=model_name, 
                                                                    report=report)
    def new_report(self):

        form = _ReportForm(self, request.form)

        if form.validate():
            def parse_filters(filters):
                result = {}
                for current in filters:
                    if current["col"] not in result:
                        result[current["col"]] = {'operator': current["op"], 'value': current["val"]}
                    else:
                        val = result[current["col"]]
                        if not isinstance(val, list):
                            val = [val]
                        val.append({'operator': current["op"], 'value': current["val"]})
                        result[current["col"]] = val
                return result
            
            name = form.name.data
            id = None
            if request.args.get('preview'):
                name += '(' + _('Preview') + ')'
                id = 0
            report_id = create_report(form.data_set, name=name, creator=form.creator.data, description=form.description.data, 
                              columns=form.columns.data, filters=parse_filters(json.loads(form.filters.data)), id = id)
            return jsonify({'id': report_id, 'name': form.name.data, 'url': url_for('.report', id_=report_id)})
        else:
            return jsonify({'errors': form.errors}), 403

class _ReportForm(Form):  
    def __init__(self, report_view, data):
        self.report_view = report_view
        super(_ReportForm, self).__init__(data)

    def validate_data_set_id(self, e):
        try:
            self.data_set = DataSet(self.report_view, e.data)
            self.columns.choices = [(str(c['idx']), c['name']) for c in self.data_set.columns]
        except OSError:
            raise validators.ValidationError('invalid dataset')

    name = TextField('name', [validators.Required()])
    creator = TextField('createor')
    description = TextField('description')
    data_set_id = IntegerField('data_set_id', [validators.Required()])
    columns = SelectMultipleField('columns', [validators.Required()], choices=[])
    filters = TextField('filters')
