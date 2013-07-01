#! /usr/bin/env python
# -*- coding: UTF-8 -*-

from flask.ext.report import utils
from basemain import app, db
import models

def main():
    from flask.ext import report
    report.FlaskReport(db, utils.collect_models(models), app)
    app.run(debug=True, port=5001, host="0.0.0.0")

if __name__ == "__main__":
    main()
