# -*- coding: UTF-8 -*-

def collect_models(module):
    ret = {}

    for k, v in module.__dict__.items():
        if hasattr(v, '_sa_class_manager'):
            ret[k] = v
    return ret
