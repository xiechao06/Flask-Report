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
        self.init_data_set()
        self.init_notification()
        return app

    def init_data_set(self):
        import yaml
        import datetime

        d = {'create_time': datetime.datetime(2013, 7, 2, 7, 30),
             'creator': u'\u667a\u51a0',
             'default_report_name': u'xxxx\u62a5\u8868',
             'description': u'\u4e09\u56fd\u65f6\u671f\u5404\u4e2a\u56fd\u5bb6\u7684\u60c5\u51b5\u5206\u6790',
             'filters': {'Group.name': {'operators': ['eq', 'ne'], 'shown': True},
                         'User.impact': {'name': u'\u5f71\u54cd\u529b', 'operators': ['eq', 'ne']},
                         'sum(User.impact)': {'operators': ['eq', 'ne']}},
             'name': u'\u4e09\u56fd\u5b9e\u529b\u62a5\u544a'}

        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_conf", "data_sets", "1")
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path, "meta.yaml"), "w") as f:
            yaml.dump(d, f, allow_unicode=True)

        pyfile = """# -*- coding: UTF-8 -*-
from sqlalchemy import func

def get_query(db, model_map):
    Group = model_map['Group']
    User = model_map['User']
    return db.session.query(Group.id.label(u'国家编号'),
                            Group.name.label(u'国家'),
                            func.sum(User.impact).label(u'总影响力'),
                            func.avg(User.impact).label(u'平均影响力'),
                            func.sum(User.intelligience).label(u'总智力'),
                            func.avg(User.intelligience).label(u'平均智力'),
                            func.sum(User.strength).label(u'总武力'),
                            func.avg(User.strength).label(u'平均武力')).group_by(User.group_id).join(User)"""
        with open(os.path.join(path, "query_def.py"), "w") as f:
            f.write(pyfile)

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
        if not os.path.exists(path):
            os.makedirs(path)
        with open(os.path.join(path, "meta.yaml"), "w") as f:
            yaml.dump(d, f, allow_unicode=True)

    def start(self):
        self.server = make_server(self.host, self.port, self.app)
        self.server.serve_forever()

    def stop(self):
        if hasattr(self, 'server'):
            self.server.shutdown()
