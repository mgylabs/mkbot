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
            new ToolStripMenuItem("설정", null, Setting), new ToolStripMenuItem("MGCert", null, MGCert), new ToolStripMenuItem("업데이트", null, checkupdate), new ToolStripMenuItem("종료", null, Exit)});
        }

        private void checkupdate(object sender, EventArgs e)
        {
            isupdate = true;
            if (online)
            {
                process.Kill();
            }
            this.notifyIcon1.Icon = Properties.Resources.mkbot_update;
            using (StreamWriter outputFile = new StreamWriter(@"pipe\pipe.txt"))
            {
                outputFile.Write("1");
            }
            while (true)
            {
                string text = File.ReadAllText(@"pipe\pipe.txt");
                if (text.Equals("0"))
                {
                    this.notifyIcon1.Icon = Properties.Resources.mkbot_off;
                    break;
                }
            }
        }

        private void notifyIcon1_MouseClick(object sender, MouseEventArgs e)
        {
            if ((!isupdate)&&(e.Button == MouseButtons.Left))
            {
                if (!online)
                {
                    process.Start();
                    this.notifyIcon1.Icon = Properties.Resources.mkbot_on;
                    online = true;
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
