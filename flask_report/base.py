# -*- coding: UTF-8 -*-
import os
from flask import render_template
from flask.ext.report.report import Report

class FlaskReport(object):

    def __init__(self, db, model_map, app, blueprint=None):
        self.db = db
        host = blueprint or app
        self.conf_dir = app.config.get("REPORT_DIR", "report_conf")
        self.report_dir = os.path.join(self.conf_dir, "reports")
        self.data_set_dir = os.path.join(self.conf_dir, "data_sets")
        self.model_map = model_map
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)
        if not os.path.exists(self.data_set_dir):
            os.makedirs(self.data_set_dir)

        host.route("/report-list/")(self.report_list)
        host.route("/report/<int:id_>")(self.report)
        host.route("/report_csv/<int:id_>")(self.report_csv)
        host.route("/report_pdf/<int:id_>")(self.report_pdf)
        host.route("/report_txt/<int:id_>")(self.report_txt)


        from flask import Blueprint
        # register it for using the templates of data browser
        self.blueprint = Blueprint("report____", __name__,
                                   static_folder="static",
                                   template_folder="templates")
        app.register_blueprint(self.blueprint, url_prefix="/__report__")


    def report_list(self):
        # directory 0 is reserved for special purpose
        reports = [Report(self, int(dir_name)) for dir_name in os.listdir(self.report_dir) if dir_name.isdigit() and dir_name != '0']
        return render_template('report____/report-list.html', reports=reports)

    def report(self, id_):
        report = Report(self, id_)
        html_report = report.html_template.render(data=report.data, columns=report.columns)
        customized_filter_condition = report.literal_filter_condition_code
        return render_template("report____/report.html", report=report, html_report=html_report, customized_filter_condition=customized_filter_condition)
    
    def report_csv(self, id_):
        # TODO unimplemented
        pass

    def report_pdf(self, id_):
        # TODO unimplemented
        pass

    def report_txt(self, id_):
        # TODO unimplemented
        pass
