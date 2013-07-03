# -*- coding: UTF-8 -*-
import os
import yaml
from import_file import import_file
from werkzeug.utils import cached_property

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

    @cached_property
    def query(self):
        query_def_file = os.path.join(self.report_view.data_set_dir, str(self.id_), "query_def.py")
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

