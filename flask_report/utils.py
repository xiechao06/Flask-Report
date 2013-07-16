# -*- coding: UTF-8 -*-
import os

import yaml
import sqlalchemy
import operator
from flask.ext.babel import _

_NONE = object()
AGGREGATE_FUNC = ["sum", "avg", "max", "min", "count"]

def collect_models(module):
    ret = {}

    for k, v in module.__dict__.items():
        if hasattr(v, '_sa_class_manager'):
            ret[k] = v
    return ret


def get_primary_key(model):
    """
        Return primary key name from a model

        :param model:
            Model class
    """
    from sqlalchemy.schema import Table

    if isinstance(model, Table):
        for idx, c in enumerate(model.columns):
            if c.primary_key:
                return c.key
    else:
        props = model._sa_class_manager.mapper.iterate_properties

        for p in props:
            if hasattr(p, 'columns'):
                for c in p.columns:
                    if c.primary_key:
                        return p.key

    return None


def get_column_operated(func):
    ret = func
    while not isinstance(ret, sqlalchemy.schema.Column):
        if isinstance(ret, sqlalchemy.sql.expression.ColumnClause):  # sub query
            ret = list(enumerate(ret.base_columns))[0][1]
        else:
            ret = ret.clauses.clauses[0]
    return ret


def query_to_sql(statement, bind=None):
    """
    print a query, with values filled in
    for debugging purposes *only*
    for security, you should always separate queries from their values
    please also note that this function is quite slow
    """
    if not statement:
        return ""
    import sqlalchemy.orm

    if isinstance(statement, sqlalchemy.orm.Query):
        if bind is None:
            bind = statement.session.get_bind(
                statement._mapper_zero_or_none()
            )
        statement = statement.statement
    elif bind is None:
        bind = statement.bind

    dialect = bind.dialect
    compiler = statement._compiler(dialect)

    class LiteralCompiler(compiler.__class__):
        def visit_bindparam(
                self, bindparam, within_columns_clause=False,
                literal_binds=False, **kwargs
        ):
            return super(LiteralCompiler, self).render_literal_bindparam(
                bindparam, within_columns_clause=within_columns_clause,
                literal_binds=literal_binds, **kwargs
            )

        def render_literal_value(self, value, type_):

            if isinstance(type_, sqlalchemy.types.DateTime) or isinstance(type_, sqlalchemy.types.Date):
                return '"' + unicode(value) + '"'
            elif isinstance(value, str):
                value = value.decode(dialect.encoding)
            return super(LiteralCompiler, self).render_literal_value(value, type_)

    compiler = LiteralCompiler(dialect, statement)
    import sqlparse

    return sqlparse.format(compiler.process(statement), reindent=True, keyword_case='upper')


def get_color(idx, colors, total_length=None, rgb=True):
    try:
        return colors[idx]
    except (IndexError, TypeError):
        def _get_color(idx, length):
            from flask.ext.report.colors import COLORS

            r = int(len(COLORS) * (idx + 1) / (length + 1))
            color = COLORS.values()[r]
            if rgb:
                return color
            else:
                return ('rgba(%s, %s, %s, 0.5)' % (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)),
                        'rgba(%s, %s, %s, 1)' % (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)))

        return _get_color(idx, total_length)


def dump_to_yaml(obj):
    import yaml

    if obj:
        result = yaml.safe_dump(obj, allow_unicode=True).decode("utf-8")
        if result[-5:] == "\n...\n":
            result = result[:-5]
    else:
        result = ''
    return result


def get_column_operator(filter_key, columns, report_view):
    col = _NONE
    try:
        if "(" not in filter_key and ")" not in filter_key:
            model_name, column_name = filter_key.split(".")
            col = operator.attrgetter(column_name)(report_view.model_map[model_name])
        else:
            import re

            model_name, column_name = re.split("[()]", filter_key)[1].split(".")
            filter_key = filter_key.replace(model_name, report_view.model_map[model_name].__table__.name)
            for c in columns:
                if filter_key == c["key"]:
                    col = c["expr"]
                    break
    except ValueError:
        for c in columns:
            if filter_key == c["name"]:
                if "(" not in c["key"] and ")" not in c["key"]:
                    model_name, column_name = c["key"].split(".")
                    col = operator.attrgetter(column_name)(report_view.table_map[model_name])
                else:
                    col = c["expr"]
                break
    finally:
        if col is _NONE:
            raise ValueError(_("No Such Column"))
        else:
            try:
                #if hasattr(col, "property") and hasattr(col.property, "direction"):
                    #col = col.property.local_remote_pairs[0][1]
                if operator.attrgetter("element.name")(col) in AGGREGATE_FUNC:
                    return col, "having"
            except AttributeError:
                pass
            return col, "filter"

def dump_yaml(path, **kwargs):
    if os.path.isfile(path):
        try:
            os.unlink(path+"~")
        except OSError:
            pass
        os.rename(path, path+"~")
    with open(path, 'w') as f:
        yaml.safe_dump(kwargs, allow_unicode=True, stream=f)
