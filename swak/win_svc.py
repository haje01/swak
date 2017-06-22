import os
import sys
import logging
from logging import config as logconfig
from datetime import datetime
import socket
import struct

import yaml
import psutil
import servicemanager
import win32event
import win32service
import win32serviceutil
import click
import errno
import netifaces


class ConmonService(win32serviceutil.ServiceFramework):
    _svc_name_ = "conmon"
    _svc_display_name_ = "Connection Monitoring Service"

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
        s = prepare_sniff(hostip)
        while rc != win32event.WAIT_OBJECT_0:
            try:
                main(s, hostip, hport, sip, sport)
            except Exception, e:
                logging.error("Service error: {}".format(e))
                break
            rc = win32event.WaitForSingleObject(self.hWaitStop, 0)
        log_footer()
        servicemanager.LogInfoMsg("Service is finished.")


@click.group()
def test_dummy():
    pass


def log_header():
    logging.critical("\t# =========== Start connection monitoring ===========")
    cfg_path = get_cfg_path()
    logging.critical("\t# Config file: '{}', hostip: {}, hport: {}, sip: {},"
                     " sport: {}".format(cfg_path, hostip, hport, sip, sport))


def log_footer():
    logging.critical("\t# =========== Finish connection monitoring ===========")


def local_pinfo_by_addr(sip, sport):
    for con in psutil.net_connections():
        if con.status != 'ESTABLISHED':
            continue

        pid = con.pid

        try:
            proc = psutil.Process(pid)
        except psutil.NoSuchProcess:
            logging.debug("\t# No such process: {}".format(pid))
            continue

        try:
            name = proc.name()
        except:
            logging.debug("\t# Fail to get process name: {}".format(pid))
            continue

        try:
            exe = proc.exe()
        except:
            logging.debug("\t# Fail to get executable for pid: {}".format(pid))
            exe = None

        ppid = proc.ppid()
        try:
            pname = psutil.Process(ppid).name() if ppid is not None else None
        except psutil.NoSuchProcess:
            pname = "_destroyed_"

        try:
            username = proc.username()
        except psutil.AccessDenied:
            username = "AccessDenied"

        ctime = datetime.fromtimestamp(proc.create_time())
        return name, pname, exe, username, ctime


def main(s, hostip, hport, sip, sport):
    res = sniff(s, hostip, hport, sip, sport)
    if res is None:
        return
    _hostip, _hport, _sip, _sport, data, datasize = res
    if datasize <= 1:
        return
    pinfo = local_pinfo_by_addr(_sip, _sport)
    if pinfo is not None:
        name, pname, exe, username, ctime = pinfo
    else:
        name, pname, exe, username, ctime = \
            None, None, None, None, None
    logging.info("\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".\
                    format(_sip, _sport, _hostip, _hport, name, exe, pname,
                           username, ctime, data.encode('string-escape')))


@click.command()
@click.argument("hostip")
@click.option("--hport", type=int, help="target host port")
@click.option("--sip", help="target source ip")
@click.option("--sport", type=int, help="target source port")
def test(hostip, hport, sip, sport):
    g = globals()
    g['hostip'] = hostip
    g['hport'] = hport
    g['sip'] = sip
    g['sport'] = sport
    log_header()
    s = prepare_sniff(hostip)
    while True:
        main(s, hostip, hport, sip, sport)

test_dummy.add_command(test)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ConmonService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        cmd = sys.argv[1]
        if cmd == 'test':
            test_dummy()
        else:
            win32serviceutil.HandleCommandLine(ConmonService)
