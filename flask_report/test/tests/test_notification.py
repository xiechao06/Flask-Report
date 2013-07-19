#-*- coding:utf-8 -*-
from pyfeature import Feature, Scenario, when, then, and_, given
from base import init


def test_notification():
    init()
    with Feature(u"测试notification", ["flask.ext.report.test.tests.steps.notification_step"]):
        with Scenario(u"初始化"):
            given(u"初始化notification")

        with Scenario(u"notification的修改"):
            browser = when(u"访问notification", id_=1)
            browser = then(u"修改notification的name成功", browser)

            browser = when(u"启用notification", browser)
            then(u"启用成功", browser)