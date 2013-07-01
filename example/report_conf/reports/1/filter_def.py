# -*- coding: UTF-8 -*-

def get_filter(db, model_map):
    Group = model_map['Group']
    return Group.name != u'吴'
