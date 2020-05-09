using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace MKBot
{
    public partial class Form1 : Form
    {
        private bool online = false;
        private ProcessStartInfo psi = new ProcessStartInfo();
        private Process process = new Process();

        public Form1()
        {
            InitializeComponent();
            psi.FileName = "app\\app.exe";
            psi.WorkingDirectory = "app";
            psi.CreateNoWindow = true;
            //psi.WindowStyle = ProcessWindowStyle.Hidden;
            psi.UseShellExecute = false;

            process.StartInfo = psi;
            process.EnableRaisingEvents = true;
            process.Exited += new EventHandler(ProcessExited);
            this.notifyIcon1.Icon = Properties.Resources.mkbot_off;
        }

        private void exitToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Application.Exit();
        }

        private void setToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Process.Start("data\\config.json");
        }

        private void notifyIcon1_MouseClick(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
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

        private void ProcessExited(object source, EventArgs e)
        {
            this.notifyIcon1.Icon = Properties.Resources.mkbot_off;
            online = false;
        }

        private void mGCertToolStripMenuItem_Click(object sender, EventArgs e)
        {
            Process.Start("data\\mgcert.json");
        }
    }
}