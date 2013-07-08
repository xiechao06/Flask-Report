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


def query_to_sql(statement, bind=None):
    """
    print a query, with values filled in
    for debugging purposes *only*
    for security, you should always separate queries from their values
    please also note that this function is quite slow
    """
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

    compiler = LiteralCompiler(dialect, statement)
    return compiler.process(statement)