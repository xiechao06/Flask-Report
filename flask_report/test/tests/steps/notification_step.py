#-*- coding:utf-8 -*-
from pyfeature import step


@step(u"初始化notification")
def _(step):
    step.feature.browser.visit("/report/schedule-list")
    import json
    d = json.loads(step.feature.browser.find_by_tag("body").html)
    assert len(d) == 0


@step(u"访问notification")
def _(step, id_):
    step.feature.browser.visit("/report/notification/%s" % id_)
    assert step.feature.browser.status_code.is_success()
    return step.feature.browser


@step(u"修改notification的name")
def _(step, browser):
    browser.fill_form({"name": "NewName"})
    browser.find_by_css(".pagination-centered").first.find_by_tag("button").first.click()
    browser.reload()
    assert browser.find_by_name("name").first.value == u"NewName"
    return browser


@step(u"启用notification")
def _(step, browser):
    browser.find_by_name("action").first.click()
    browser.reload()
    return browser


@step(u"启用成功")
def _(step, browser):
    assert browser.find_by_name("action").first.value == u"Disable"
    browser.visit("/report/schedule-list")
    import json
    d = json.loads(browser.find_by_tag("body").html)
    assert len(d) == 1