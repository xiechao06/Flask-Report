from contextlib import contextmanager
from urlparse import urlparse
from unittest import TestCase
from pyfeature import before_each_feature, after_each_feature
from splinter import Browser
import testconfig
import unittest


class BrowserRunner(object):
    """
        Wrapper around splinter.Browser.

        All attribute access that isn't to anything that starts with underscore
        will be proxied to an instance of Browser.

        It also has a custom visit that can take in a normal url
        , and using scheme, hostname and port from testconfig will construct
        a complete url to use with the actual visit function.

        Also has _open_browser and _close_browser for setup and teardown.
    """
    def __init__(self, hostname, scheme, port):
        self._port = port
        self._scheme = scheme
        self._hostname = hostname

    @classmethod
    def from_testconfig(cls):
        """Create an instance of BrowserRunner using values from testconfig"""
        port = testconfig.config.get('port', 3000)
        scheme = testconfig.config.get('scheme', 'http')
        hostname = testconfig.config.get('hostname', 'localhost') 
        return cls(hostname, scheme, port)

    @classmethod
    def as_fixture(cls):
        """
            Create a tuple of (browser, setup, tearDown)
            Used to conveniently make file level test fixtures
        """
        instance = cls.from_testconfig()
        setup = lambda : instance._open_browser()
        teardown = lambda : instance._close_browser()
        return instance, setup, teardown

    def _open_browser(self):
        self._browser = Browser()

    def _close_browser(self):
        self._browser.quit()

    def visit(self, url):
        """Custom visit command that takes port, schema and hostname on the runner into account"""
        if '://' not in url and not url.startswith('/'):
            url = "/{}".format(url)

        if url.startswith('/'):
            url = "{}://{}:{}{}".format(self._scheme, self._hostname, self._port, url)

        return self._browser.visit(url)

    def __getattr__(self, key):
        """Proxy everything to the browser object"""
        if key.startswith("_"):
            return object.__getattribute__(self, key)

        browser = self._browser
        if hasattr(browser, key):
            return getattr(browser, key)

        return object.__getattribute__(self, key)


def init():
    """Custom TestCase that starts a browser for every test"""
    @before_each_feature
    def setup(feature):
        """Create our browser"""
        feature.browser = BrowserRunner.from_testconfig()
        feature.browser._open_browser()

    @after_each_feature
    def teardown(feature):
        """Make sure the browser dies"""
        feature.browser._close_browser()
