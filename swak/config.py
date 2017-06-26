"""Select config file and parse."""
import os
import sys
import logging

import yaml


ENVVAR = 'SWAK_CFG'
CFG_FNAME = 'config.yml'


def get_execfg_path():
    """Get config file path with regard to executable environment.

    Decide config directory with following rules:
        1. If package has been freezed, used dir of freezed executable path,
        2. Or use the dir of current module.

    Then make full path by join directory & config file name.

    Returns:
        str: Absolute path to config file.
    """
    if getattr(sys, 'frozen', False):
        bdir = os.path.dirname(sys.executable)
    else:
        bdir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(bdir, CFG_FNAME)


def cfg_exist_in_exedir():
    path = get_execfg_path()
    return os.path.isfile(path)


def select_and_parse(_cfgpath=None):
    """Select config file and parse it.

    Config file selection rule:
        1. If `_cfgpath` is given, use it.
        2. If an environment variable exists for cfg, use it.
        3. If a cfg file exist in the executable's directory, use it.
        4. Error

    Args:
        _cfgpath (str): Force config path

    Returns:
        dict: Parsed config dictionary
    """
    logging.info("config.select_and_parse: _cfgpath {}".format(_cfgpath))
    cfgpath = _select(_cfgpath)
    return _parse(cfgpath)


def _select(_cfgpath=None):
    if _cfgpath is not None:
        cfgpath = _cfgpath
    elif ENVVAR in os.environ:
        cfgpath = os.environ[ENVVAR]
    elif cfg_exist_in_exedir():
        cfgpath = get_execfg_path()
    else:
        raise Exception("Config file not exist!")
    return cfgpath


def _parse(cfgpath):
    logging.info("config.parse config: {}".format(cfgpath))
    with open(cfgpath, 'r') as f:
        cfg = yaml.load(f)
    logging.info("Parsed Config: {}".format(cfg))
    return cfg
