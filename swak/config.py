"""Select config file and parse."""
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


def _get_exe_dir():
    if getattr(sys, 'frozen', False):
        bdir = os.path.dirname(sys.executable)
    else:
        bdir = os.path.dirname(os.path.abspath(__file__))
    return bdir


def _get_home_dir():
    bdir = os.environ.get('SWAK_HOME')
    if bdir is not None:
        return bdir
    logging.info("No explicit SWAK_HOME, use exe directory as home.")
    return _get_exe_dir()


def _home_cfg_exists():
    path = os.path.join(_get_home_dir(), CFG_FNAME)
    return os.path.isfile(path)


def get_home_cfgpath():
    """Get config file path with regard to home directory.

    Decide config directory with following rules:
        1. If package has been freezed, used dir of freezed executable path,
        2. Or use the dir of current module.

    Then make full path by join directory & config file name.

    Returns:
        str: Absolute path to config file.
    """
    bdir = _get_home_dir()
    return os.path.join(bdir, CFG_FNAME)


def select_and_parse(_cfgpath=None):
    """Select config file and parse it.

    Config file selection rule:
        1. If explicit `_cfgpath` is given, use it.
        2. If an environment variable for home dir(`SWAK_HOME`) exists, infer
            from it.
        3. If a cfg file exist in the executable's directory, use it.
        4. Error

    To resolve environment variables in the file, this function takes
    following procedures.
        1. Parsing config file without resolving EnvVars
        2. Exposure some of config vars to EnvVars
        3. Resolve EnvVars in the original config, then parse it.

    Args:
        _cfgpath (str): Force config path

    Returns:
        dict: Parsed config dictionary
    """
    logging.info("config.select_and_parse: _cfgpath {}".format(_cfgpath))
    cfgpath = _select(_cfgpath)

    with open(cfgpath, 'r') as f:
        raw = f.read()
        cfg = yaml.load(raw)
        _exposure_to_envvars(cfg)

        expanded = raw.format(**os.environ)
        cfg = yaml.load(expanded)
        expanded_log = DEFAULT_LOG_CFG.format(**os.environ)
        lcfg = yaml.load(expanded_log)
        _update_dict(cfg, lcfg)
        return cfg


def _exposure_to_envvars(cfg):
    os.environ['SWAK_SVC_NAME'] = cfg['svc_name']
    swak_home = os.environ['SWAK_HOME'] if 'SWAK_HOME' in os.environ else\
        _get_exe_dir()
    os.environ['SWAK_HOME'] = swak_home


def _select(_cfgpath=None, check_exists=True):
    if _cfgpath is not None:
        cfgpath = _cfgpath
        if check_exists and not os.path.isfile(cfgpath):
            raise IOError("File '{}' from parameter does not exist".format(cfgpath))
    elif ENVVAR in os.environ:
        cfgpath = get_home_cfgpath()
        if check_exists and not os.path.isfile(cfgpath):
            raise IOError("'config.yml' not exist in SWAK_HOME")
    elif _home_cfg_exists():
        cfgpath = get_home_cfgpath()
        if check_exists and not os.path.isfile(cfgpath):
            raise IOError("'config.yml' not exist in '{}'".format(_get_home_dir()))
    else:
        raise ValueError("Config file was not provided!")
    logging.info("Selected config '{}'".format(cfgpath))
    return cfgpath
