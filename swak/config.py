"""This module implements config."""

import os
import sys
import logging
from collections import Mapping

import yaml

from swak.exception import ConfigError
from swak.util import parse_and_validate_cmds, validate_tag

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
        2. If explicit `SWAK_EXE_DIR` exists in envvar, use it.
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
    """Decide config file path and parse its config.

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
        2. If an environment variable(`SWAK_HOME`) exists, use it.
        3. If the executable's directory has config file, use it.
        4. Error
    """
    def config_file_exists(adir):
        return os.path.isfile(os.path.join(adir, CFG_FNAME))

    logging.debug("select_home")
    if _home is not None:
        logging.debug("  explicit home {}".format(_home))
        home = _home
        if check_config and not config_file_exists(home):
            raise IOError("Home directory '{}' from parameter does not have"
                          " config file.".format(home))
    elif ENVVAR in os.environ:
        home = os.environ.get('SWAK_HOME')
        logging.debug("  envvar home {}".format(home))
        if check_config and not config_file_exists(home):
            raise IOError("SWAK_HOME does not have config file.")
    elif config_file_exists(get_exe_dir()):
        logging.debug("  exedir {} has config".format(get_exe_dir()))
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


def validate_cfg(cfg):
    """Validate config content."""
    from swak.event_router import Rule

    def check_souce_input(v):
        if not v.startswith('i.'):
            raise ConfigError("A source should start with input "
                              "plugin.")

    source_tags = set()
    match_tags = set()
    # souces
    if 'sources' not in cfg:
        raise ConfigError("No 'sources' field exists in config.")
    if cfg['sources'] is None:
        raise ConfigError("'sources' field has no declaration.")
    if type(cfg['sources']) is not list:
        raise ConfigError("The value of the 'sources' field must be a "
                          "list.")
    for srccmds in cfg['sources']:
        if type(srccmds) is not str:
            raise ConfigError("The value of the each source must be a string.")
        try:
            cmds = parse_and_validate_cmds(srccmds, True)
        except ValueError as e:
            raise ConfigError(e)
        tag = cmds[-1][-1]
        validate_tag(tag)
        source_tags.add(tag)
        first = cmds[0][0]
        check_souce_input(first)

    # maches
    if 'matches' in cfg:
        matches = cfg['matches']
        if matches is None:
            raise ConfigError("'matches' field has no declaration.")
        if type(matches) is not dict:
            raise ConfigError("The value of the 'matches' field must be a "
                              "dictionary content.")
        for tag, match_cmds in matches.items():
            try:
                validate_tag(tag)
                if type(match_cmds) is not str:
                    raise ConfigError("each match must be a string.")
                cmds = parse_and_validate_cmds(match_cmds, False)
            except ValueError as e:
                raise ConfigError(e)
            match_tags.add(tag)

    for stag in source_tags:
        for mtag in match_tags:
            if Rule(mtag, None).match(stag) is None:
                raise ConfigError("source tag '{}' does not have corresponding"
                                  " match tag.".format(stag))
