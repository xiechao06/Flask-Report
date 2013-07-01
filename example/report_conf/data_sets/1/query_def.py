# -*- coding: UTF-8 -*-
from sqlalchemy import func

def get_query(db, model_map):
    Group = model_map['Group']
    User = model_map['User']
    return db.session.query(Group.name, func.avg(User.impact).label(u'平均影响力'), func.avg(User.intelligience).label(u'平均智力'), func.avg(User.strength).label(u'平均武力')).group_by(User.group_id).join(User)
