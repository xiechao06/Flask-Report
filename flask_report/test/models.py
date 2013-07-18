# -*- coding: UTF-8 -*-
from datetime import datetime
from app import db

user_and_group_table = db.Table('TB_ASSOCIATION',
                                db.Column('user_id', db.Integer,
                                          db.ForeignKey('TB_USER.id')),
                                db.Column('group_id', db.Integer,
                                          db.ForeignKey('TB_GROUP.id')))


class User(db.Model):
    __tablename__ = "TB_USER"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey("TB_GROUP.id"), nullable=False)
    group = db.relationship("Group", backref="users")
    create_time = db.Column(db.DateTime, default=datetime.now, doc=u"创建于")
    strength = db.Column(db.Integer, nullable=False)
    impact = db.Column(db.Integer, nullable=False)
    intelligience = db.Column(db.Integer, nullable=False)
    is_lord = db.Column(db.Boolean, default=False)

    def __unicode__(self):
        return self.name

class Group(db.Model):
    __tablename__ = "TB_GROUP"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True, doc=u"用户组名称")

    def __unicode__(self):
        return self.name


class Car(db.Model):
    __tablename__ = "TB_CAR"

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(32))
    owner_id = db.Column(db.Integer, db.ForeignKey("TB_USER.id"))
    owner = db.relationship(User, backref="car_list")

    def __unicode__(self):
        return self.model

