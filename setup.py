#!/usr/bin/env python

__version__ = '0.1.0'

from distutils.core import setup

setup(
    name='swak',
    version=__version__,
    author="JeongJu Kim",
    author_email='haje01@gmail.com',
    url="https://github.com/haje01/swak",
    description="Multi-OS Monitoring Agent in Python",
    platforms=["any"],
    packages=['swak'],
    license=['MIT License'],
    install_requires=[
        'click',
    ],
    dependency_links=[
        'git+http//github.com/serverdensity/python-daemon.git#egg=python_daemon',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
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
