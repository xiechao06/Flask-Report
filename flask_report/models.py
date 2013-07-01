# -*- coding: UTF-8 -*-

from datetime import datetime

def setup_models(db):

    class DataSet(db.Model):
        __tablename__ = "TB_DATA_SET"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        creator = db.Column(db.String)
        create_time = db.Column(db.DateTime, default=datetime.now)

        def __unicode__(self):
            return self.name

    class Report(db.Model):
        __tablename__ = "TB_REPORT"
        
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        creator = db.Column(db.String)
        data_set_id = db.Column(db.Integer, db.ForeignKey(DataSet.id), nullable=False)
        data_set = db.relationship(DataSet)
        create_time = db.Column(db.DateTime, default=datetime.now)

        def __unicode__(self):
            return self.name

    class FilterCond(db.Model):

        __tablename__ = "TB_FILTER_COND"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        value = db.Column(db.String, nullable=False)
        report = db.relationship(Report, backref="filter_conditions")
        report_id = db.Column(db.Integer, db.ForeignKey(Report.id), nullable=False)

    class OrderBy(db.Model):

        __tablename__ = "TB_ORDER_BY"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        desc = db.Column(db.Boolean)
        report = db.relationship(Report, backref=db.backref("order_by", uselist=False))
        report_id = db.Column(db.Integer, db.ForeignKey(Report.id), nullable=False)

    d = globals()
    d['DataSet'] = DataSet
    d['Report'] = Report
    d['FilterCond'] = FilterCond
    d['OrderBy'] = OrderBy
