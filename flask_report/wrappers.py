# -*- coding: UTF-8 -*-

import os
import operator
import json
import codecs
from itertools import izip
from jinja2 import Template
from werkzeug.utils import cached_property
from import_file import import_file
from sqlalchemy import desc

class ReportWrapper(object):

    def __init__(self, report_view, report):
        self.report_view = report_view
        self.report = report

    @property
    def columns(self):
        columns_file = file(os.path.join(self.report_view.report_dir, str(self.report.id), "columns.json"))
        ret = DataSetWrapper(self.report_view, self.report.data_set).columns
        return [ret[i] for i in json.loads(columns_file.read())]

    @property
    def data(self):
        data_set_wrapper = DataSetWrapper(self.report_view, self.report.data_set)
        q = data_set_wrapper.query
        for fc in self.report.filter_conditions:
            model_name, column_name = fc.name.split('.')
            q = q.filter(operator.attrgetter(column_name)(self.report_view.model_map[model_name])==fc.value)
        if self.literal_filter_condition:
            q = q.filter(self.literal_filter_condition)
        all_columns = dict((c['name'], c) for c in data_set_wrapper.columns)
        if self.report.order_by:
            order_by = all_columns.get(self.report.order_by.name, None)
            if order_by:
                order_by = order_by['expr']
                if self.report.order_by.desc:
                    order_by = desc(order_by)
                q = q.order_by(order_by)
        return q.all()

    @cached_property
    def literal_filter_condition(self):
        filter_def_file = os.path.join(self.report_view.report_dir, str(self.report.id), "filter_def.py")
        if os.path.exists(filter_def_file):
            lib = import_file(filter_def_file)
            return lib.get_filter(self.report_view.db, self.report_view.model_map)

    @property
    def html_template(self):
        report_file = os.path.join(self.report_view.report_dir, str(self.report.id), "report.html")
        return Template(file(report_file).read())

    def read_literal_filter_condition(self):
        filter_def_file = os.path.join(self.report_view.report_dir, str(self.report.id), "filter_def.py")
        if os.path.exists(filter_def_file):
            return codecs.open(filter_def_file, encoding='utf-8').read()

class DataSetWrapper(object):

    def __init__(self, report_view, data_set):
        self.report_view = report_view
        self.data_set = data_set

    @cached_property
    def query(self):
        query_def_file = os.path.join(self.report_view.data_set_dir, str(self.data_set.id), "query_def.py")
        lib = import_file(query_def_file)
        return lib.get_query(self.report_view.db, self.report_view.model_map)

    @cached_property
    def columns(self):
        def _make_dict(idx, c):
            if hasattr(c['expr'], '_element'): # is label
                name = c['name'] or dict(name=str(c['expr']))
                key = c['expr']._element.name
            else:
                name = str(c['expr'])
                key = name
            
            return dict(idx=idx, name=name, key=key, expr=c['expr'])

        return tuple(_make_dict(idx, c) for idx, c in enumerate(self.query.column_descriptions))
