using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MKBot
{
    class TrayApp : ApplicationContext
    {
        private NotifyIcon notifyIcon1;
        private ContextMenuStrip contextMenuStrip1;

        private bool online = false;
        private bool isupdate = false;
        private bool existnew = false;
        private ProcessStartInfo psi = new ProcessStartInfo();
        private Process process = new Process();

        public TrayApp()
        {
            psi.FileName = "app\\app.exe";
            psi.WorkingDirectory = "app";
            psi.CreateNoWindow = true;
            psi.UseShellExecute = false;
            process.StartInfo = psi;
            process.EnableRaisingEvents = true;
            process.Exited += new EventHandler(ProcessExited);

            this.notifyIcon1 = new NotifyIcon();
            this.contextMenuStrip1 = new ContextMenuStrip();

            this.notifyIcon1.ContextMenuStrip = this.contextMenuStrip1;
            this.notifyIcon1.MouseClick += new MouseEventHandler(this.notifyIcon1_MouseClick);
            this.notifyIcon1.Text = "MK Bot";
            this.notifyIcon1.Visible = true;
            this.notifyIcon1.Icon = Properties.Resources.mkbot_off;

            this.contextMenuStrip1.Items.AddRange(new ToolStripItem[] {
            new ToolStripMenuItem("설정", null, Setting), new ToolStripMenuItem("MGCert", null, MGCert), new ToolStripMenuItem("업데이트", null, clickcheckupdate), new ToolStripMenuItem("종료", null, Exit)});
        }

        private void showToast(string title, string text)
        {
            this.notifyIcon1.BalloonTipTitle = title;
            this.notifyIcon1.BalloonTipText = text;
            this.notifyIcon1.ShowBalloonTip(0);
        }

        private int Run_msu(string argv = "")
        {
            ProcessStartInfo psi2 = new ProcessStartInfo();
            Process p2 = new Process();

            psi2.FileName = "Update\\Mulgyeol Software Update.exe";
            psi2.Arguments = argv;
            psi2.WorkingDirectory = "Update";
            psi2.CreateNoWindow = true;
            psi2.UseShellExecute = false;
            p2.StartInfo = psi2;
            if (argv.Equals("")) 
            {
                this.notifyIcon1.Visible = false;
            }
            p2.Start();
            p2.WaitForExit();
            int result = p2.ExitCode;
            return result;
        }

        private void clickcheckupdate(object sender, EventArgs e)
        {
            checkupdate();
        }

        private void checkupdate()
        {
            isupdate = true;
            if (online)
            {
                process.Kill();
            }

            this.notifyIcon1.Icon = Properties.Resources.mkbot_update;
            int result = Run_msu();

            if (result == 1)
            {
                this.notifyIcon1.Visible = true;
                this.notifyIcon1.Icon = Properties.Resources.mkbot_off;
                isupdate = false;
                showToast("Mulgyeol Software Update", "소프트웨어가 이미 최신 버전입니다.");
            }
        }

        private void notifyIcon1_MouseClick(object sender, MouseEventArgs e)
        {
            if ((!isupdate)&&(e.Button == MouseButtons.Left))
            {
                if (!online)
                {
                    this.notifyIcon1.Icon = Properties.Resources.mkbot_on;
                    process.Start();
                    online = true;
                    int reuslt = Run_msu("/c");
                    if (reuslt == 0)
                    {
                        this.existnew = true;
                    }
                }
                else
                {
                    process.Kill();
                }
            }
        }

        private void ProcessExited(object sender, EventArgs e)
        {
            this.notifyIcon1.Icon = Properties.Resources.mkbot_off;
            online = false;
            if (this.existnew)
            {
                checkupdate();
            }

        }

        private void Setting(object source, EventArgs e)
        {
            Process.Start("data\\config.json");
        }

        private void MGCert(object source, EventArgs e)
        {
            Process.Start("data\\mgcert.json");
        }

        private void Exit(object source, EventArgs e)
        {
            this.notifyIcon1.Visible = false;
            Application.Exit();
        }
    }
}
