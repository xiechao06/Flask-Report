"""
Flask-Report
-----

Flask-Report is a micro report framework based on Flask, and other report engines

````````````

.. code:: python

from flask import Flask
from database import db
app = Flask(__name__)

form flask_report import FlaskReport
FlaskReport(db, app)

Links
`````

* `website <http://www.github.com/xiechao06/Flask-Report/>`_
* `documentation <http://xiechao06.github.io/Flask-Report/>`_
* `development version
<http://github.com/xiechao06/flask/zipball/master#egg=Flask-Report-dev>`_

"""
from __future__ import print_function
from setuptools import Command, setup

class run_audit(Command):
    """Audits source code using PyFlakes for following issues:
- Names which are used but not defined or used before they are defined.
- Names which are redefined without having been used.
"""
    description = "Audit source code with PyFlakes"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import os, sys
        try:
            import pyflakes.scripts.pyflakes as flakes
        except ImportError:
            print("Audit requires PyFlakes installed in your system.")
            sys.exit(-1)

        warns = 0
        # Define top-level directories
        dirs = ('flask_report', 'example')
        for dir in dirs:
            for root, _, files in os.walk(dir):
                for file in files:
                    if file != '__init__.py' and file.endswith('.py') :
                        warns += flakes.checkPath(os.path.join(root, file))
        if warns > 0:
            print("Audit finished with total %d warnings." % warns)
        else:
            print("No problems found in sourcecode.")

setup(
    name='flask_report',
    version='0.0.1-dev',
    url='http://github.com/xiechao06/Flask-Report/',
    license='BSD',
    author='XieChao',
    author_email='xiechao06@gmail.com',
    description='A micro report system based upon flask and some report engines',
    long_description=__doc__,
    packages=['flask_report'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    # install_requires=open('requirements.txt').readlines(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: REPORT',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    cmdclass={'audit': run_audit},
)
