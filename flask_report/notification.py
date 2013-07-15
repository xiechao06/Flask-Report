# -*- coding: UTF-8 -*-
import os
import codecs
from collections import namedtuple

from import_file import import_file
from datetime import date

import yaml
from flask.ext.report.report import Report

class Notification(object):

    def __init__(self, report_view, id_):
        self.report_view = report_view
        self.id_ = id_

        meta_file = os.path.join(self.report_view.notification_dir, str(id_), 'meta.yaml')
        meta = yaml.load(file(meta_file).read())
        self.name = meta['name']
        self.creator = meta.get('creator')
        self.create_time = meta.get('create_time')
        self.description = meta.get("description")
        self.senders = meta.get('senders')
        self.report_ids = meta.get('report_ids')
        self.__subject = meta.get('subject')
        self._crontab = meta.get('crontab')
        self.enabled = meta.get('enabled')

    @property
    def template(self):
        template_file = os.path.join(self.report_view.notification_dir, str(self.id_), "template.html")
        if not os.path.exists(template_file):
            # read the default template
            return self.report_view.app.jinja_env.get_template("report____/default_notification.html")
        return self.report_view.app.jinja_env.from_string(codecs.open(template_file, encoding='utf-8').read())

    @property
    def subject(self):
        return self.report_view.app.jinja_env.from_string(self.__subject).render(date=date.today(), notification=self)

    @property 
    def reports(self):
        return [Report(self.report_view, id_) for id_ in self.report_ids]   


    @property
    def crontab(self):
        CronTab = namedtuple('CronTab', ['minute', 'hour', 'day', 'month', 'day_of_week'])
        return CronTab(*self._crontab.split())

    def dump(self):
        meta_file = os.path.join(self.report_view.notification_dir, str(self.id_), 'meta.yaml')
        d = {
            'name': self.name,
            'creator': self.creator,
            'create_time': self.create_time,
            'description': self.description,
            'senders': self.senders,
            'report_ids': self.report_ids,
            'subject': self.__subject,
            'crontab': self._crontab,
            'enabled': self.enabled
        }
        yaml.dump(d, open(meta_file, 'w'))
