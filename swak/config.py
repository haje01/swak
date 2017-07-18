"""Select config file and parse.
"""
import os
import sys
import logging
from collections import Mapping

import yaml


ENVVAR = 'SWAK_HOME'
CFG_FNAME = 'config.yml'
DEFAULT_LOG_CFG = '''
logger:
    version: 1

    formatters:
        simpleFormater:
            format: '%(asctime)s %(threadName)s [%(levelname)s] - %(message)s'
            datefmt: '%Y-%m-%d %H:%M:%S'

    handlers:
        console:
            class: logging.StreamHandler
            formatter: simpleFormater
            level: DEBUG
            stream: ext://sys.stdout
        file:
            class: logging.handlers.RotatingFileHandler
            formatter: simpleFormater
            level: DEBUG
            filename: '{SWAK_HOME}/logs/{SWAK_SVC_NAME}-log.txt'
            maxBytes: 10485760
            backupCount: 10

    root:
        level: DEBUG
        handlers: [console, file]
'''


def _update_dict(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = _update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def get_exe_dir():
    """Get swak executable's directory.

    Decide config directory with following rules:
        1. If package has been freezed, used dir of freezed executable path,
        2. If explit `SWAK_EXE_DIR` exists in envvar, use it.
        3. Use the dir of current module.

    Then make full path by join directory & config file name.

    Returns:
        str: Absolute path to config file.
    """
    if getattr(sys, 'frozen', False):
        bdir = os.path.dirname(sys.executable)
    elif 'SWAK_EXE_DIR' in os.environ:
        return os.environ['SWAK_EXE_DIR']
    else:
        bdir = os.path.dirname(os.path.abspath(__file__))
    return bdir


def select_and_parse(_home=None):
    """Get config path and parse its config.

    To resolve environment variables while parsing config file, this function
    takes following procedures.
        1. Parsing config file without resolving EnvVars
        2. Exposure some of config vars to EnvVars
        3. Resolve EnvVars in the original config, then parse it.

    Args:
        _home (str): Force home directory

    Returns:
        str: Selected home directory
        dict: Parsed config dictionary
    """
    logging.info("select_and_parse: _home {}".format(_home))
    home = select_home(_home)
    cfgpath = os.path.join(home, CFG_FNAME)

    with open(cfgpath, 'r') as f:
        raw = f.read()
        cfg = yaml.load(raw)
        _exposure_to_envvars(cfg)

        expanded = raw.format(**os.environ)
        cfg = yaml.load(expanded)
        expanded_log = DEFAULT_LOG_CFG.format(**os.environ)
        lcfg = yaml.load(expanded_log)
        _update_dict(cfg, lcfg)
        return home, cfg


def get_config_path(home=None, check_config=False):
    """Select home directory and make config path with it.

    Args:
        home (str): Force home directory

    Returns:
        str: config file path in selected home
    """
    home = select_home(home, check_config)
    return os.path.join(home, CFG_FNAME)


def _exposure_to_envvars(cfg):
    os.environ['SWAK_SVC_NAME'] = cfg['svc_name']
    swak_home = os.environ['SWAK_HOME'] if 'SWAK_HOME' in os.environ else\
        get_exe_dir()
    os.environ['SWAK_HOME'] = swak_home


def select_home(_home=None, check_config=True):
    """Select home directory and parse its config.

    Home directory selection rule:
        1. If explicit `_home` is given, use it.
        2. If an environment variable for home dir(`SWAK_HOME`) exists, use it.
        3. If the executable's directory has config file, use it.
        4. Error
    """
    def config_file_exists(adir):
        return os.path.isfile(os.path.join(adir, CFG_FNAME))

    if _home is not None:
        home = _home
        if check_config and not config_file_exists(home):
            raise IOError("Home directory '{}' from parameter does not have"
                          " config file.".format(home))
    elif ENVVAR in os.environ:
        home = os.environ.get('SWAK_HOME')
        if check_config and not config_file_exists(home):
            raise IOError("SWAK_HOME does not have config file.")
    elif config_file_exists(get_exe_dir()):
        home = get_exe_dir()
    else:
        raise ValueError("Home directory can't be decided!")

    logging.info("Selected home '{}'".format(home))
    return home


def get_pid_path(home, svc_name):
    """Get pid path with regards home and service name."""
    pid_name = 'swak.pid' if svc_name is None else '{}.pid'.format(svc_name)
    pid_path = os.path.join(home, 'run', pid_name)
    return pid_path
