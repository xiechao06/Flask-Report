#-*- coding:utf-8 -*-
from contextlib import contextmanager
import threading
from flask import Flask, request
from splinter import Browser
import unittest
from werkzeug.serving import make_server

class App(object):
    def __init__(self, port=5000, host='localhost'):
        self.port = port
        self.host = host
        self.app = self.setup_app()

    def setup_app(self):
        app = Flask(__name__)
        app.config["TEST"] = True
        app.route('/')(self.root)
        app.route('/lol')(self.lol)
        app.route('/some_javascript')(self.some_javascript)
        return app

    def lol(self):
        return "lol{}".format(request.args.get("num"))

    def root(self):
        return 'root'

    def some_javascript(self):
        return """
<html>
<head>
<script type="text/javascript">
function clicked() {
var thing = document.createElement("p")
, text = document.createTextNode("clicked")
;
thing.appendChild(text);
document.body.appendChild(div);
}
</script>
</head>
<body>
<button id="clicker" onclick="clicked()">Click ME!</button>
</body>
</html>
"""

    def start(self):
        self.server = make_server(self.host, self.port, self.app)
        self.server.serve_forever()

    def stop(self):
        if hasattr(self, 'server'):
            self.server.shutdown()

    def url(self, url):
        return "%s://%s:%d%s" % ("http", self.host, self.port, url)


@contextmanager
def test_server():
    '''Start a server to test against'''
    app = App()
    try:
        thread = threading.Thread(target=app.start)
        thread.daemon = True
        thread.start()
        yield app
    finally:
        app.stop()


class MyTest(unittest.TestCase):
    def test_connect(self):
        with test_server() as a:
            browser = Browser()
            browser.visit(a.url("/"))

