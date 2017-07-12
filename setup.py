#!/usr/bin/env python
import os

with open(os.path.join('swak', 'version.py'), 'rt') as f:
    version = f.read().strip()

__version__ = version

from distutils.core import setup

SCRIPTS = ['bin/swak']
if os.name == 'nt':
    SCRIPTS += ['bin/swak.bat']

setup(
    name='swak',
    version=__version__,
    author="JeongJu Kim",
    author_email='haje01@gmail.com',
    url="https://github.com/haje01/swak",
    description="Multi-purpose Monitoring Agent in Python",
    platforms=["any"],
    packages=['swak', 'swak/plugins'],
    scripts=SCRIPTS,
    license=['MIT License'],
    install_requires=[
        'click',
        'pyyaml',
        'future',
    ],
    dependency_links=[
        'https://github.com/serverdensity/python-daemon/master#egg='
        'python_daemon',
    ],
    extras_require={
        'dev': [
            'pytest',
            'coverage',
            'pyinstaller',
            'tox',
        ],
    },
    keywords=['system'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Environment :: No Input/Output (Daemon)',
        'Development Status :: 2 - Pre-Alpha',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Monitoring',
    ]
)
