# -*- coding: UTF-8 -*-

import os
import operator
import copy
import codecs
from collections import namedtuple
from itertools import izip
from functools import partial
import datetime
import shutil

import sqlalchemy
from flask import render_template, url_for
import yaml
from import_file import import_file
from flask.ext.report.data_set import DataSet
from flask.ext.report.utils import get_primary_key, get_column_operated
from werkzeug.utils import cached_property
from jinja2 import Template
from sqlalchemy import desc, select


class Report(object):
    def __init__(self, report_view, id_):
        self.report_view = report_view
        self.id_ = id_
        report_meta_file = os.path.join(self.report_view.report_dir, str(id_), 'meta.yaml')
        report_meta = yaml.load(file(report_meta_file).read())
        self.name = report_meta['name']
        self.creator = report_meta.get('creator')
        self.create_time = report_meta.get('create_time')
        self.filters = report_meta.get('filters')
        self.description = report_meta.get("description")
        self.data_set = DataSet(report_view, report_meta['data_set_id'])
        self.__columns = report_meta.get('columns')
        self.__special_chars = {"gt": operator.gt, "lt": operator.lt, "ge": operator.ge, "le": operator.le,
                                "eq": operator.eq, "ne": operator.ne}
        self._sum_columns = report_meta.get("sum_columns", [])
        self._avg_columns = report_meta.get("avg_columns", [])
        bars = report_meta.get("bar", [])
        self._bar = bars if isinstance(bars, list) else [bars]
        pies = report_meta.get("pie", [])
        self._pie = pies if isinstance(pies, list) else [pies]
        self._bar_charts = None
        self._pie_charts = None
        self._searchable_columns = report_meta.get("searchable_columns", [])

    @cached_property
    def columns(self):
        all_columns = self.data_set.columns
        ret = []
        for i in self.__columns:
            col = copy.copy(all_columns[i])
            col['get_drill_down_link'] = lambda r: None

            if os.path.isdir(os.path.join(self.report_view.report_dir, str(self.id_), "drill_downs", str(i))):
                col['get_drill_down_link'] = partial(self._gen_drill_down_link, i)
            if not self._searchable_columns or i in self._searchable_columns:
                col["searchable"] = True
            ret.append(col)
        return ret

    def _gen_drill_down_link(self, col_id, r):
        group_by_columns = self.query.statement._group_by_clause.clauses
        if group_by_columns:
            params = {}
            d = dict((col['key'], col) for col in self.data_set.columns)

            for col in group_by_columns:
                if col.foreign_keys:
                    remote_side = list(enumerate(col.foreign_keys))[0][1].column
                    col_name = remote_side.table.name + "." + remote_side.name
                else:
                    col_name = str(col)
                    if isinstance(col, sqlalchemy.sql.expression.Function):
                        col_name = col_name.replace('"', '')
                params[col_name] = r[d[col_name]['idx']]
            return url_for('.drill_down_detail', report_id=self.id_, col_id=col_id, **params)
        else:
            return None

    @property
    def sum_columns(self):
        all_columns = self.data_set.columns
        return [all_columns[i] for i in self._sum_columns]

    @property
    def sum_column_index(self):
        def generate():
            for row in sorted(self._sum_columns):
                for idx, column in enumerate(self.columns):
                    if column["idx"] == row:
                        yield idx
        return list(generate())

    @property
    def avg_columns(self):
        all_columns = self.data_set.columns
        return [all_columns[i] for i in self._avg_columns]

    def _get_operator_and_value(self, value):
        if isinstance(value, dict) and value.get("operator"):
            return self.__special_chars[value["operator"]], value.get("value")
        else:
            return operator.eq, value

    @cached_property
    def query(self):
        q = self.data_set.query
        if self.filters:
            from flask.ext.report.utils import get_column_operator
            for name, params in self.filters.items():
                column, op_ = get_column_operator(name, self.data_set.columns, self.report_view)
                if hasattr(column, "property") and hasattr(column.property, "direction"):
                    column = column.property.local_remote_pairs[0][1]
                if not isinstance(params, list):
                    params = [params]
                for param in params:
                    operator_, value = self._get_operator_and_value(param)
                    if op_ == "filter":
                        q = q.filter(operator_(column, value))
                    elif op_ == "having":
                        q = q.having(operator_(column, value))
        if self.literal_filter_condition is not None:
            q = q.filter(self.literal_filter_condition)
        all_columns = dict((c['name'], c) for c in self.data_set.columns)
        return q

    @property
    def data(self):
        return self.query.all()

    @cached_property
    def literal_filter_condition(self):
        filter_def_file = os.path.join(self.report_view.report_dir, str(self.id_), "filter_def.py")
        if os.path.exists(filter_def_file):
            lib = import_file(filter_def_file)
            return lib.get_filter(self.report_view.db, self.report_view.model_map)

    @property
    def html_template(self):
        report_file = os.path.join(self.report_view.report_dir, str(self.id_), "report.html")
        if not os.path.exists(report_file):
            # read the default report template
            return self.report_view.app.jinja_env.get_template("report____/default_html_report.html")
        return self.report_view.app.jinja_env.from_string(codecs.open(report_file, encoding='utf-8').read())

    def read_literal_filter_condition(self):
        filter_def_file = os.path.join(self.report_view.report_dir, str(self.id_), "filter_def.py")
        if os.path.exists(filter_def_file):
            return codecs.open(filter_def_file, encoding='utf-8').read()

    @property
    def short_description(self):
        return render_template('report____/report_short_description.html', report=self)

    def get_drill_down_detail_template(self, col_id):
        template_file = os.path.join(self.report_view.report_dir, str(self.id_), "drill_downs", str(col_id), "template.html")
        if not os.path.exists(template_file):
            # read the default template
            return self.report_view.app.jinja_env.get_template("report____/default_drill_down_html_report.html")
        return self.report_view.app.jinja_env.from_string(codecs.open(template_file, encoding='utf-8').read())

    def get_drill_down_detail(self, col_id, **filters):
        lib = import_file(os.path.join(self.report_view.report_dir, str(self.id_), "drill_downs", str(col_id), "objects.py"))
        return lib.objects(self.report_view.db, self.report_view.model_map, **filters)
    
    @property
    def sum_fields(self):
        return [{"col": column["name"], "value": sum(d[column["idx"]] or 0 for d in self.data)} for column in
                self.sum_columns]

    @property
    def avg_fields(self):
        return [{"col": column["name"], "value": sum((d[column["idx"]] or 0) for d in self.data) / len(self.data)} for column
                in self.avg_columns]

    @property
    def bar_charts(self):
        if self._bar_charts is None:
            import uuid

            self._bar_charts = []
            all_columns = self.data_set.columns
            for bar_chart in self._bar:
                data = {}
                bar_columns = bar_chart.get("columns", [])
                colors = bar_chart.get("colors", [])
                columns = [all_columns[i] for i in bar_columns]
                for column in columns:
                    labels = data.setdefault("labels", [])
                    if column["name"] not in labels:
                        labels.append(column["name"])
                display_names = []
                length = len(self.data)
                for idx, i in enumerate(self.data):
                    from flask.ext.report.utils import get_color
                    color1, color2 = get_color(idx, colors, length, False)
                    dataset = {"fillColor": color1, "strokeColor": color2, "data": [int(i[c["idx"]]) for c in columns]}
                    display_columns = bar_chart.get("display_columns", [])
                    name = "(" + ", ".join(unicode(i[all_columns[c]['idx']]) for c in display_columns) + ')'
                    display_names.append(
                        {"name": name, "color": color1})
                    datasets = data.setdefault("datasets", [])
                    datasets.append(dataset)
                self._bar_charts.append({"name": bar_chart.get("name"), "id_": uuid.uuid1(), "data": data,
                                         "display_names": display_names})
        return self._bar_charts

    @property
    def pie_charts(self):
        if self._pie_charts is None:
            import uuid

            all_columns = self.data_set.columns
            self._pie_charts = []
            for pie in self._pie:
                pie_column_idx = pie.get("column")
                column = all_columns[pie_column_idx]
                colors = pie.get("colors", [])
                data = []
                display_names = []
                length = len(self.data)
                total = sum(row[column["idx"]] for row in self.data)
                for idx, row in enumerate(self.data):
                    from flask.ext.report.utils import get_color
                    color = get_color(idx, colors, length)
                    data.append({"value": row[column["idx"]], "color": color})
                    display_columns = pie.get("display_columns", [])
                    name = "(" + ", ".join(unicode(row[all_columns[c]['idx']]) for c in display_columns) + ')'
                    display_names.append({"name": name, "color": color,
                                          "distribution": "%.2f%%" % (row[column["idx"]] * 100.0 / total)})
                result = {"name": pie.get("name"), "id_": uuid.uuid1(), "display_names": display_names, "data": data}
                self._pie_charts.append(result)
        return self._pie_charts

def create_report(data_set, name, description="", creator="", create_time=None, columns=None, filters=None, id=None):

    create_time = create_time or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    columns = columns or [c['idx'] for c in data_set.columns]
    filters = filters or {}
    
    if id is None:
        all_report_dirs = [dir for dir in os.listdir(data_set.report_view.report_dir) if dir.isdigit()]
        if not all_report_dirs:
            new_report_id = 0
        else:
            new_report_id = max([int(dir) for dir in all_report_dirs]) + 1
    else:
        new_report_id = id

    new_report_dir = os.path.join(data_set.report_view.report_dir, str(new_report_id))
    if not os.path.exists(new_report_dir):
        os.mkdir(new_report_dir)

    converted_filters = {}
    for k, v in filters.items():
        if v['proxy']:
            converted_filters.update(data_set.proxy_filter_map[k](v['value']))
        else:
            converted_filters[k] = v

    with file(os.path.join(new_report_dir, "meta.yaml"), "w") as f:
        dict_ = {
            'name': name,
            'data_set_id': data_set.id_,
            'description': description,
            'creator': creator,
            'create_time': create_time,
            'columns': [int(c) for c in columns],
            'filters': converted_filters,
        }
        yaml.safe_dump(dict_, allow_unicode=True, stream=f)

    if os.path.exists(os.path.join(data_set.dir, 'drill_downs')):
        shutil.rmtree(os.path.join(new_report_dir, 'drill_downs'), ignore_errors=True)
        shutil.copytree(os.path.join(data_set.dir, 'drill_downs'), os.path.join(new_report_dir, 'drill_downs'))
    return new_report_id
