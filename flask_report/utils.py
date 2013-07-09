# -*- coding: UTF-8 -*-
import sqlalchemy

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
        if isinstance(ret, sqlalchemy.sql.expression.ColumnClause): # sub query
            ret = list(enumerate(ret.base_columns))[0][1]
        else:
            ret = ret.clauses.clauses[0]
    return ret
