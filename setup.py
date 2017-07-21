#!/usr/bin/env python
import os

with open(os.path.join('swak', 'version.py'), 'rt') as f:
    version = f.read().strip()
    version = version.split('=')[1].strip('"')

__version__ = version

from distutils.core import setup

SCRIPTS = ['bin/swak']
if os.name == 'nt':
    SCRIPTS += ['bin/swak.bat']


def package_dirs(directory):
    dirs = []
    for adir in os.listdir(directory):
        path = os.path.join(directory, adir)
        if os.path.isfile(path):
            continue
        if '__pycache__' in path:
            continue
        initpy = os.path.join(path, '__init__.py')
        if not os.path.isfile(initpy):
            continue
        dirs.append(path)
    return dirs

from subprocess import check_output
print(check_output(['pwd']))
print(check_output(['ls', '-alh']))
plugin_dirs = package_dirs('swak/plugins')
plugins = [adir.replace(os.path.sep, '.') for adir in plugin_dirs]

setup(
    name='swak',
    version=__version__,
    author="JeongJu Kim",
    author_email='haje01@gmail.com',
    url="https://github.com/haje01/swak",
    description="Multi-purpose Monitoring Agent in Python",
    platforms=["any"],
    packages=['swak', 'swak.plugins'] + plugins,
    scripts=SCRIPTS,
    license=['MIT License'],
    install_requires=[
        'click',
        'pyyaml',
        'future',
        'tabulate',
    ],
    dependency_links=[
        'http://github.com/serverdensity/python-daemon/master#egg=python_daemon',
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
