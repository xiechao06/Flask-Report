#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from basemain import db
from flask.ext.report import models as builtin_models
builtin_models.setup_models(db)
import models
db.create_all()

def commit(obj):
    db.session.add(obj)
    db.session.commit()
    return obj


Wei = commit(models.Group(name=u"魏"))
Shu = commit(models.Group(name=u"蜀"))
Wu = commit(models.Group(name=u"吴"))

CaoCao = commit(models.User(name=u"曹操", strength=60, intelligience=90, impact=90, group=Wei, is_lord=True))
GouJia = commit(models.User(name=u'郭嘉', strength=10, intelligience=90, impact=30, group=Wei))
DianWei = commit(models.User(name=u'典韦', strength=90, intelligience=20, impact=30, group=Wei))
LiuBei = commit(models.User(name=u"刘备", strength=50, intelligience=75, impact=85, group=Shu, is_lord=True))
ZhuGeLiang = commit(models.User(name=u'诸葛亮', strength=10, intelligience=90, impact=60, group=Shu))
GuanYu = commit(models.User(name=u'关羽', strength=90, intelligience=70, impact=50, group=Shu) )
ZhangFei = commit(models.User(name=u'张飞', strength=90, intelligience=50, impact=30, group=Shu))
SunQuan = commit(models.User(name=u"孙权", strength=65, intelligience=70, impact=80, group=Wu, is_lord=True))
ZhouYu = commit(models.User(name=u'周瑜', strength=60, intelligience=90, impact=60, group=Wu))
LuSu = commit(models.User(name=u'鲁肃', strength=10, intelligience=85, impact=50, group=Wu))

data_set1 = commit(builtin_models.DataSet(name="dataset 1"))
report1 = commit(builtin_models.Report(name="report 1", creator="James T. Kirk", data_set=data_set1))
filter_cond1 = commit(builtin_models.FilterCond(name="User.is_lord", value=False, report=report1))
order_by1 = commit(builtin_models.OrderBy(name=u"平均影响力", desc=True, report=report1))
