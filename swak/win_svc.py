#!/usr/bin/env python
import sys
import logging
import traceback
from logging import config as logconfig

import servicemanager
import win32event
import win32service
import win32serviceutil
import click

from swak.config import select_and_parse
from swak.util import init_home, check_python_version
from swak.cli import main
from swak.version import VERSION

check_python_version()


def prog_name():
    if getattr(sys, 'frozen', False):
        return "swaksvc.exe"
    else:
        return "win_svc.py"


def show_usage():
    print("Swak version {}".format(VERSION))
    print("================== Swak Commands  ==================")
    ctx = click.Context(main, info_name="{} cli".format(prog_name()))
    print(ctx.get_help())
    print()
    sys.argv = [prog_name()]
    print("================= Service Commands =================")
    win32serviceutil.HandleCommandLine(None)


# Handle help / cli command beforehand (No need to parse config)
if len(sys.argv) > 2:
    cmd = sys.argv[1]
    if cmd == 'help':
        show_usage()
    elif cmd == 'cli':
        main(obj={}, prog_name="{} cli".format(prog_name()), args=sys.argv[2:])
        sys.exit()


home, cfg = select_and_parse(None)
# init required directories
init_home(home, cfg)
# init logger
logconfig.dictConfig(cfg['logger'])


class SwakService(win32serviceutil.ServiceFramework):
    _svc_name_ = cfg['svc_name']
    _svc_display_name_ = cfg['svc_dname']

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        servicemanager.LogInfoMsg("Service is stopping.")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogInfoMsg("Service is starting.")
        rc = None
        log_header()
        while rc != win32event.WAIT_OBJECT_0:
            try:
                pass
            except Exception:
                for l in traceback.format_exc().splitlines():
                    logging.error(l)
                break
            rc = win32event.WaitForSingleObject(self.hWaitStop, 0)
        log_footer()
        servicemanager.LogInfoMsg("Service is finished.")


def log_header():
    logging.critical("=============== Start service ===============")
    # cfg_path = get_cfg_path()


def log_footer():
    logging.critical("=============== Finish service ===============")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SwakService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SwakService)
