# -*- coding: UTF-8 -*-
import codecs
import os
import operator
import yaml
from import_file import import_file
from werkzeug.utils import cached_property
import sqlalchemy
from flask.ext.babel import _

_NONE = object()
_TYPES = {"str": "text", "int": "number", "bool": "checkbox", "datetime": "datetime", "date": "date"}


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
        self._filters = data_set_meta.get("filters", {})

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

    def get_query(self, filters):

        def get_operator(op):
            return self.__special_chars[op]

        query = self.query
        from flask.ext.report.utils import get_column_operator

        for filter_ in filters:
            column, op_ = get_column_operator(filter_["col"], self.columns, self.report_view)
            if op_ == "filter":
                method_ = query.filter
            elif op_ == "having":
                method_ = query.having

            if hasattr(column, "property") and hasattr(column.property, "direction"):
                column = column.property.local_remote_pairs[0][1]
            query = method_(get_operator(filter_["op"])(column, filter_["val"]))
        return query

    @property
    def filters(self):
        def get_label_name(name, column):
            if not name:
                for c in self.columns:
                    if c["key"] == str(column.expression) or c["expr"] == column:
                        name = c["name"]
                        break
                else:
                    name = _("Unknown")
            return name

        def _get_type(type_, default=None):
            import types
            if isinstance(default, types.TypeType):
                default = _TYPES.get(default.__name__)
            else:
                default = default or "text"
            return _TYPES.get(type_, default)

        filters = []
        from flask.ext.report.utils import get_column_operator

        for k, v in self._filters.items():
            column, op_ = get_column_operator(k, self.columns, self.report_view)
            default = None
            try:
                default = column.type.python_type
            except NotImplementedError:
                pass
            except AttributeError:
                default = "select"

            result = {"name": get_label_name(v.get("name"), column), "col": k, "ops": v.get("operators"),
                      "type": _get_type(v.get("value_type"), default)}
            if hasattr(column, "property") and hasattr(column.property, "direction"):
                def _iter_choices(column):
                    model = column.property.mapper.class_
                    from flask.ext.report.utils import get_primary_key
                    pk = get_primary_key(model)
                    for row in self.report_view.db.session.query(model):
                        yield getattr(row, pk), unicode(row)
                result["opts"] = list(_iter_choices(column))
            filters.append(result)
        return filters

    def get_current_filters(self, currents):
        def _match(to_matcher):
            result = to_matcher.copy()
            for filter in self.filters:
                if to_matcher["col"] == filter["col"]:
                    result.update(filter)
                    return result

        all = []
        for current in currents:
            filter_ = _match(current)
            if filter_:
                try:
                    filter_["val"] = int(filter_["val"])
                except ValueError:
                    pass
                all.append(filter_)
        return all

    def parse_filters(self, filters):
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
