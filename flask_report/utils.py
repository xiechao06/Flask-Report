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
    if isinstance(func, sqlalchemy.sql.expression.ColumnElement): # sub query
        func = list(enumerate(func.base_columns))[0][1]
    return func.clauses.clauses[0]
