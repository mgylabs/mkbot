import servicemanager
import socket
import sys, os
import win32event
import win32service
import win32serviceutil
import win32api
import subprocess

class MulgyeolUpdateService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MulgyeolUpdateService"
    _svc_display_name_ = "Mulgyeol Update Service"
    _svc_description_ = "MK Bot Update"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.filepath = os.getenv('LOCALAPPDATA')+'\\Programs\\MK Bot\\pipe\\pipe.txt'

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        rc = None
        while rc != win32event.WAIT_OBJECT_0:
            self.main()
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)

    def main(self):
        with open(self.filepath, 'rt') as f:
            res = f.read()
        if res == '1':
            # win32api.ShellExecute(None, "open", "schtasks.exe", '/RUN /TN MKBotUpdate', None, 0)
            ecode = subprocess.call([os.getenv('LOCALAPPDATA')+'\\Programs\\MK Bot\\Update\\Mulgyeol Software Update.exe'])
            if ecode == 1:
                with open(self.filepath, 'wt') as f:
                    f.write('0')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MulgyeolUpdateService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MulgyeolUpdateService)