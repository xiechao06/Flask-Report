#-*- coding:utf-8 -*-
from pyfeature import Feature, Scenario, when, then
from base import init


def test_it_works():
    init()
    with Feature(u"测试data_set的filter", ['flask.ext.report.test.tests.steps.data_set_step']):
        with Scenario(u"加载data_set"):
            browser = when(u"打开dataset", id_=1)
            then(u"配置shown的filter展示", browser)

        with Scenario(u"删除data_set的filter"):
            browser = when(u"打开dataset", id_=1)
            then(u"删除filter", browser)

        with Scenario(u"删除data_set的filter"):
            browser = when(u"打开dataset", id_=1)
            then(u"添加filter", browser)
