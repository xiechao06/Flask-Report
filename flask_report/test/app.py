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

        return app

    def start(self):
        self.server = make_server(self.host, self.port, self.app)
        self.server.serve_forever()

    def stop(self):
        if hasattr(self, 'server'):
            self.server.shutdown()
