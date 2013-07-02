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
    report.FlaskReport(db, utils.collect_models(models), app, report_page)
    app.register_blueprint(report_page, url_prefix="/report")
    app.run(debug=True, port=5001, host="0.0.0.0")

if __name__ == "__main__":
    main()
