# -*- coding: UTF-8 -*-
import os
import tempfile
from werkzeug.serving import make_server
import flask
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class App(object):
    def __init__(self, port=3000, host='localhost'):
        self.port = port
        self.host = host
        self.app = self.setup_app()

    def setup_app(self):
        app = flask.Flask(__name__)
        from flask.ext.report import FlaskReport, utils

        report_page = flask.Blueprint("report", __name__, static_folder="static",
                                      template_folder="templates")
        db_fd, db_fname = tempfile.mkstemp()
        os.close(db_fd)
        app.config["SECRET_KEY"] = "JHdkj1adf;"
        app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
        from flask.ext.babel import Babel
        Babel(app)
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
        db.init_app(app)
        db.app = app
        import models
        db.create_all()
        FlaskReport(db, utils.collect_models(models), app, report_page, table_label_map={'TB_USER': u'角色'})
        app.register_blueprint(report_page, url_prefix="/report")
        self.init_notification()
        return app

    def init_notification(self):
        d = {'crontab': '1 * * * *',
             'description': '',
             'enabled': False,
             'name': u'班组绩效报表通知',
             'report_ids': [2],
             'senders': ['abc549825@163.com'],
             'subject': '[{{date}}]{{ notification.name }}'}
        import yaml
        import os

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_conf", "notifications", "1")
        with open(os.path.join(path, "meta.yaml"), "w") as f:
            yaml.dump(d, f, allow_unicode=True)

    def start(self):
        self.server = make_server(self.host, self.port, self.app)
        self.server.serve_forever()

    def stop(self):
        if hasattr(self, 'server'):
            self.server.shutdown()
