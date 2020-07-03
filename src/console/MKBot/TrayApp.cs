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
        private bool checking_update = false;
        private bool can_update = false;
        private ProcessStartInfo psi1 = new ProcessStartInfo();
        private Process app_process = new Process();
        private ProcessStartInfo psi2 = new ProcessStartInfo();
        private Process msu_process = new Process();

        private ToolStripMenuItem UpdateMenu;

        public TrayApp()
        {
            Environment.CurrentDirectory = Path.GetDirectoryName(Application.ExecutablePath);
            psi1.FileName = "app\\app.exe";
            psi1.WorkingDirectory = "app";
            psi1.CreateNoWindow = true;
            psi1.UseShellExecute = false;
            app_process.StartInfo = psi1;
            app_process.EnableRaisingEvents = true;
            app_process.Exited += new EventHandler(ProcessExited_app);

            psi2.FileName = "app\\Mulgyeol Software Update.exe";           
            psi2.WorkingDirectory = "app";
            psi2.CreateNoWindow = true;
            psi2.UseShellExecute = false;
            msu_process.StartInfo = psi2;
            msu_process.EnableRaisingEvents = true;
            msu_process.Exited += new EventHandler(ProcessExited_msu);

            notifyIcon1 = new NotifyIcon();
            contextMenuStrip1 = new ContextMenuStrip();

            notifyIcon1.ContextMenuStrip = contextMenuStrip1;
            notifyIcon1.MouseClick += new MouseEventHandler(notifyIcon1_MouseClick);
            notifyIcon1.Text = "MK Bot";
            notifyIcon1.Visible = true;
            notifyIcon1.Icon = Properties.Resources.mkbot_off;

            UpdateMenu = new ToolStripMenuItem("업데이트 확인", null, Click_Update);

            contextMenuStrip1.Items.AddRange(new ToolStripItem[] {
            new ToolStripMenuItem("설정", null, Click_Setting), new ToolStripMenuItem("MGCert", null, Click_MGCert), UpdateMenu, new ToolStripMenuItem("종료", null, Click_Exit)});
        }

        //UI
        private void notifyIcon1_MouseClick(object sender, MouseEventArgs e)
        {
            if ((!checking_update) && (e.Button == MouseButtons.Left))
            {
                if (!online)
                {
                    notifyIcon1.Icon = Properties.Resources.mkbot_on;
                    app_process.Start();
                    online = true;
                    if (!can_update)
                    {
                        Run_msu("/c");
                    }
                }
                else
                {
                    app_process.Kill();
                }
            }
        }

        private void Click_Setting(object source, EventArgs e)
        {
            Process.Start("data\\config.json");
        }

        private void Click_MGCert(object source, EventArgs e)
        {
            Process.Start("data\\mgcert.json");
        }

        private void Click_Update(object sender, EventArgs e)
        {
            if (can_update)
            {
                if (online)
                {
                    app_process.Kill();
                } 
                else
                {
                    Run_setup(true);
                }
            }
            else
            {
                checking_update = true;
                UpdateMenu.Enabled = false;
                UpdateMenu.Text = "업데이트 다운로드 중...";
                Run_msu("/c");
            }
        }

        private void Click_Exit(object source, EventArgs e)
        {
            notifyIcon1.Visible = false;
            if (can_update)
            {
                if (online)
                {
                    app_process.Kill();
                }
                else
                {
                    Run_setup(false);
                }
            }
            Environment.Exit(0);
        }

        private void ShowToast(string title, string text)
        {
            notifyIcon1.BalloonTipTitle = title;
            notifyIcon1.BalloonTipText = text;
            notifyIcon1.ShowBalloonTip(0);
        }

        //background
        private void Run_msu(string argv = "/c")
        {
            UpdateMenu.Enabled = false;
            UpdateMenu.Text = "업데이트 다운로드 중...";
            psi2.Arguments = argv;
            try
            {
                if (msu_process.HasExited)
                {
                    msu_process.Start();
                }
            }
            catch (Exception)
            {
                msu_process.Start();
            }
        }

        private void Run_setup(bool autorun)
        {
            string param;
            if (autorun)
            {
                param = "/S /autorun";
            }
            else
            {
                param = "/S";
            }
            notifyIcon1.Visible = false;
            Process.Start(Environment.GetEnvironmentVariable("TEMP") + "\\mkbot-update\\MKBotSetup.exe", param);
            Environment.Exit(0);
        }

        private void ProcessExited_msu(object sender, EventArgs e)
        {
            if (msu_process.ExitCode == 0)
            {
                can_update = true;
                UpdateMenu.Enabled = true;
                UpdateMenu.Text = "다시 시작 및 업데이트";
                if (checking_update)
                {
                    ShowToast("Mulgyeol Software Update", "최신 업데이트를 적용하려면 MK Bot을(를) 다시 시작하세요.");
                    checking_update = false;
                }
            }
            else if (msu_process.ExitCode == 1)
            {
                UpdateMenu.Enabled = true;
                UpdateMenu.Text = "업데이트 확인";
                if (checking_update)
                {
                    ShowToast("Mulgyeol Software Update", "소프트웨어가 이미 최신 버전입니다.");
                    checking_update = false;
                }
            }
        }

        private void ProcessExited_app(object sender, EventArgs e)
        {
            notifyIcon1.Icon = Properties.Resources.mkbot_off;
            online = false;
            if (can_update)
            {
                Run_setup(true);
            }
            if (app_process.ExitCode == 1)
            {
                ShowToast("TOKEN 값이 올바르지 않습니다.", "설정을 클릭하여 올바른 TOKEN 값을 설정하세요.");
            }
        }

        internal void Application_Exit(object sender, EventArgs e)
        {
            try
            {
                if (!app_process.HasExited)
                {
                    app_process.Kill();
                }
            }
            catch (Exception) { }
        }
    }
}
