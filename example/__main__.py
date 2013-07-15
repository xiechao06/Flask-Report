#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from flask.ext.report import utils
from basemain import app, db
import models

def main():
    from flask.ext import report
    from flask import Blueprint
    report_page = Blueprint("report", __name__, static_folder="static", 
                            template_folder="templates")
    d = dict(MAIL_SERVER='smtp.163.com',
             MAIL_PORT=25,
             MAIL_USE_TLS=False,
             MAIL_USE_SSL=False,
             MAIL_USERNAME='lite_mms@163.com',
             MAIL_PASSWORD='ahKee7ic')
    for k, v in d.items():
        app.config[k] = v
    report.FlaskReport(db, utils.collect_models(models), app, report_page, table_label_map={'TB_USER': u'角色'})
    app.register_blueprint(report_page, url_prefix="/report")
    app.run(debug=True, port=5001, host="0.0.0.0")

if __name__ == "__main__":
    main()
