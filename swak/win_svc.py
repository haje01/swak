import sys
import logging
import traceback

import servicemanager
import win32event
import win32service
import win32serviceutil
import click


from swak.config import select_and_parse


cfg = select_and_parse()


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
            except Exception as e:
                for l in traceback.format_exc().splitlines():
                    logging.error(l)
                break
            rc = win32event.WaitForSingleObject(self.hWaitStop, 0)
        log_footer()
        servicemanager.LogInfoMsg("Service is finished.")


@click.group()
def cli():
    pass


def log_header():
    logging.critical("========== Start service ==========")
    # cfg_path = get_cfg_path()


def log_footer():
    logging.critical("========== Finish service ==========")


def main():
    pass


@cli.command()
def test():
    while True:
        main()


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SwakService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        cmd = sys.argv[1]
        if cmd == 'test':
            cli()
        else:
            win32serviceutil.HandleCommandLine(SwakService)
