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
            if isinstance(type_, sqlalchemy.types.DateTime):
                return '"' + str(value) + '"'
            return super(LiteralCompiler, self).render_literal_value(value, type_)

    compiler = LiteralCompiler(dialect, statement)
    return compiler.process(statement)
