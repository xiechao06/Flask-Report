#-*- coding:utf-8 -*-
from pyfeature import step


@step(u"打开dataset")
def _(step, id_):
    step.feature.browser.visit("/report/data-set/%s" % id_)
    assert step.feature.browser.status_code.is_success()
    return step.feature.browser


@step(u"配置shown的filter展示")
def _(step, browser):
    assert len(browser.find_by_name("filter")) == 1


@step(u"删除filter")
def _(step, browser):
    browser.find_by_name("remove-tr").click()
    assert len(browser.find_by_name("filter")) == 0


@step(u"添加filter")
def _(step, browser):
    length = len(browser.find_by_name("filter"))
    browser.find_by_tag("legend")[1].find_by_tag("button").first.click()
    browser.click_link_by_partial_text(u"国家")
    assert len(browser.find_by_name("filter")) == length + 1
    tds = browser.find_by_name("filter").first.find_by_tag("td")
    assert tds[1].text == u"国家"
    select = tds[2].find_by_tag("select").first
    options = select.find_by_tag("option")
    assert len(options) == 2
    assert {u"等于", u"不等于"} == set([o.text for o in options])