# -*- coding: UTF-8 -*-

import os
import operator
import codecs
from collections import namedtuple

import yaml
from import_file import import_file
from flask.ext.report.data_set import DataSet
from werkzeug.utils import cached_property
from jinja2 import Template
from sqlalchemy import desc

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
        self.order_by = report_meta.get('order_by')
        if self.order_by:
            if self.order_by.startswith('-'):
                name = self.order_by[1:]
                desc_ = True
            else:
                name = self.order_by
                desc_ = False
            self.order_by = namedtuple("OrderBy", ['name', 'desc'])(name, desc_)
        self.data_set = DataSet(report_view, report_meta['data_set_id'])
        self.__columns = report_meta.get('columns')

    @property
    def columns(self):
        all_columns = self.data_set.columns
        return [all_columns[i] for i in self.__columns]

    @property
    def data(self):
        q = self.data_set.query
        for name, value in self.filters.items():
            model_name, column_name = name.split('.')
            q = q.filter(operator.attrgetter(column_name)(self.report_view.model_map[model_name])==value)
        if self.literal_filter_condition:
            q = q.filter(self.literal_filter_condition)
        all_columns = dict((c['name'], c) for c in self.data_set.columns)
        if self.order_by:
            order_by = all_columns.get(self.order_by.name, None)
            if order_by:
                order_by = order_by['expr']
                if self.order_by.desc:
                    order_by = desc(order_by)
                q = q.order_by(order_by)
        return q.all()

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
            report_file = os.path.join(self.report_view.report_dir, '0', "report.html")
        return Template(file(report_file).read())

    def read_literal_filter_condition(self):
        filter_def_file = os.path.join(self.report_view.report_dir, str(self.id_), "filter_def.py")
        if os.path.exists(filter_def_file):
            return codecs.open(filter_def_file, encoding='utf-8').read()
