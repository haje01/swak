import sys
import logging
import traceback
from logging import config as logconfig

import servicemanager
import win32event
import win32service
import win32serviceutil

from swak.config import select_and_parse
from swak.util import init_home, check_python_version
from swak.cli import main


check_python_version()


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
    logging.critical("========== Start service ==========")
    # cfg_path = get_cfg_path()


def log_footer():
    logging.critical("========== Finish service ==========")


#@click.command(help="Test in no service mode.")
#@click.option('--home', type=click.Path(exists=True), help="Home directory")
#@click.option('--task', type=int, default=1, show_default=True, help="Task"
              #" number to test.")
#@click.option('--version', is_flag=True, help="Show Swak version.")
#def test(home, task, version):
    #test_run(home, task, version)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SwakService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        cmd = sys.argv[1]

        if cmd == 'cli':
            main(obj={}, args=sys.argv[2:])
        else:
            win32serviceutil.HandleCommandLine(SwakService)
