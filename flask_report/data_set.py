# -*- coding: UTF-8 -*-
import codecs
import os
import operator
import yaml
from import_file import import_file
from werkzeug.utils import cached_property
import sqlalchemy
from flask.ext.babel import _

class DataSet(object):

    def __init__(self, report_view, id_):
        self.report_view = report_view
        self.id_ = id_
        data_set_meta_file = os.path.join(self.report_view.data_set_dir, str(id_), 'meta.yaml')
        data_set_meta = yaml.load(file(data_set_meta_file).read())
        self.name = data_set_meta['name'] 
        self.creator = data_set_meta.get('creator')
        self.create_time = data_set_meta.get('create_time')
        self.description = data_set_meta.get("description")
        self.__special_chars = {"gt": operator.gt, "lt": operator.lt, "ge": operator.ge, "le": operator.le,
                                "eq": operator.eq, "ne": operator.ne}
        self._filters = data_set_meta.get("filters")

    @cached_property
    def query(self):
        query_def_file = os.path.join(self.report_view.data_set_dir, str(self.id_), "query_def.py")
        lib = import_file(query_def_file)
        return lib.get_query(self.report_view.db, self.report_view.model_map)

    @cached_property
    def columns(self):
        def _make_dict(idx, c):
            if hasattr(c['expr'], 'element'): # is label
                name = c['name'] or dict(name=str(c['expr']))
                key = str(c['expr'].element)
                if isinstance(c['expr'].element, sqlalchemy.sql.expression.Function):
                    key = key.replace('"', '')
            else:
                name = str(c['expr'])
                key = c['expr'].table.name + "." + c['expr'].name
            
            return dict(idx=idx, name=name, key=key, expr=c['expr'])

        return tuple(_make_dict(idx, c) for idx, c in enumerate(self.query.column_descriptions))

    @property
    def html_template(self):
        report_file = os.path.join(self.report_view.data_set_dir, str(self.id_), "data_set.html")
        if not os.path.exists(report_file):
            # read the default report template
            return self.report_view.app.jinja_env.get_template("report____/default_data_set_html.html")
        return self.report_view.app.jinja_env.from_string(codecs.open(report_file, encoding='utf-8').read())

    def get_query(self, filters):
        def get_column(column):
            for c in self.columns:
                if column == c["name"]:
                    model_name, column_name = c["key"].split(".")
                    return operator.attrgetter(column_name)(self.report_view.table_map[model_name])
            else:
                raise ValueError(_("no such column"))

        def get_operator(op):
            return self.__special_chars[op]

        query = self.query
        for filter in filters:
            query = query.filter(get_operator(filter["op"])(get_column(filter["col"]), filter["val"]))

        return query

    @property
    def filters(self):
        def _get_type(type):
            types = {"str": "text", "int": "number", "bool": "checkbox", "datetime": "datetime", "date": "date"}
            return types.get(type, "text")

        filters = []
        for k, v in self._filters.items():
            filters.append(
                {"name": v.get("name"), "col": k, "ops": v.get("operators"), "type": _get_type(v.get("value_type"))})
        return filters

    def get_current_filters(self, currents):
        def _match(to_matcher):
            result = to_matcher.copy()
            for filter in self.filters:
                if to_matcher["col"] == filter["name"]:
                    result.update(filter)
                    return result
        all = []
        for current in currents:
            filter = _match(current)
            if filter:
                all.append(filter)
        return all

    def parse_filters(self, currents):
        filters = {}
        for current in self.get_current_filters(currents):
            if current["col"] not in filters:
                filters[current["col"]] = {'operator': current["op"], 'value': current["val"]}
            else:
                val = filters[current["col"]]
                if not isinstance(val, list):
                    val = [val]
                val.append({'operator': current["op"], 'value': current["val"]})
                filters[current["col"]] = val
        return yaml.safe_dump(filters,allow_unicode=True).decode("utf-8")
