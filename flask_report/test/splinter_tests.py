#!/usr/bin/env python
"""
    Start our flask server and then run the splinter tests against it
"""
from contextlib import contextmanager
from nose import main as nose_main
import threading
import argparse
import sys

from app import App


def make_parser():
    """Make cli options"""
    parser = argparse.ArgumentParser(description="Example flask splinter tests")
    parser.add_argument("--port", help="Port of our test server", default=3000)
    parser.add_argument("--hostname", help="Hostname of our test server", default='localhost')
    parser.add_argument("--scheme", help="Scheme of our test server", default='http')
    return parser


@contextmanager
def test_server(port):
    """Start a server to test against"""
    app = App(port=port)
    try:
        thread = threading.Thread(target=app.start)
        thread.daemon = True
        thread.start()
        yield app
    finally:
        app.stop()


def run_tests(port, hostname, scheme, remaining):
    """Run the splinter tests in a new process"""
    args = ["nosetests", "--tc=port:{}".format(port), "--tc=scheme:{}".format(scheme),
            "--tc=hostname:{}".format(hostname)]
    nose_main(argv=args + remaining)


def main(argv=None):
    """Start our server and run the tests"""
    if argv is None:
        argv = sys.argv[1:]

    parser = make_parser()
    args, remaining = parser.parse_known_args(argv)

    with test_server(args.port):
        args = (args.port, args.hostname, args.scheme, remaining)
        thread = threading.Thread(target=run_tests, args=args)
        thread.start()
        thread.join()

# Make sure nosetests doesn't think this file is a test
__test__ = False

if __name__ == '__main__':
    main()
