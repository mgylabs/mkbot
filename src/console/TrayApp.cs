using Microsoft.QueryStringDotNET;
using Microsoft.Toolkit.Uwp.Notifications;
using Newtonsoft.Json.Linq;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.AccessControl;
using System.Windows.Forms;
using Windows.UI.Notifications;

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
        private Form Infowin;

        private string DirectoryPath;
        private string UserDataPath;
        private string[] args;

        public TrayApp()
        {
#if DEBUG
            DirectoryPath = Path.GetFullPath(Environment.CurrentDirectory+"\\..");
            Environment.CurrentDirectory = DirectoryPath + "\\build";
#else
            DirectoryPath = Path.GetDirectoryName(Application.ExecutablePath);
            Environment.CurrentDirectory = DirectoryPath;
#endif
            args = Environment.GetCommandLineArgs();
            if (args.Contains("--debug"))
            {
                UserDataPath = "..\\data";
            }
            else
            {
                UserDataPath = Environment.GetEnvironmentVariable("LOCALAPPDATA") + "\\Mulgyeol\\Mulgyeol MK Bot\\data";
            }
            Infowin = new InfoForm();
            var jsonString = File.ReadAllText(UserDataPath + "\\config.json");
            JObject configjson = JObject.Parse(jsonString);
            
            psi1.FileName = "app\\app.exe";
            psi1.WorkingDirectory = "app";
            psi1.CreateNoWindow = true;
            psi1.UseShellExecute = false;
            if (args.Contains("--debug"))
            {
                psi1.Arguments = "--debug";
            }
            app_process.StartInfo = psi1;
            app_process.EnableRaisingEvents = true;
            app_process.Exited += new EventHandler(ProcessExited_app);
            psi2.FileName = "app\\msu.exe";
            psi2.WorkingDirectory = "app";
            psi2.CreateNoWindow = true;
            psi2.UseShellExecute = false;
            msu_process.StartInfo = psi2;

            notifyIcon1 = new NotifyIcon();
            contextMenuStrip1 = new ContextMenuStrip();

            notifyIcon1.ContextMenuStrip = contextMenuStrip1;
            notifyIcon1.MouseClick += new MouseEventHandler(notifyIcon1_MouseClick);
            notifyIcon1.Text = "MK Bot";

            UpdateMenu = new ToolStripMenuItem("Check for Updates...", null, Click_Update);

            contextMenuStrip1.Items.AddRange(new ToolStripItem[] {
            new ToolStripMenuItem("Settings", null, Click_Setting), new ToolStripMenuItem("MGCert", null, Click_MGCert), new ToolStripMenuItem("Extensions", null, Click_Extensions), new ToolStripSeparator(), UpdateMenu, new ToolStripMenuItem("About", null, Click_info), new ToolStripSeparator(), new ToolStripMenuItem("Exit", null, Click_Exit)});

            Run_msu("/s");
            msu_process.WaitForExit();

            if (msu_process.ExitCode == 0)
            {
                Run_setup(true);
            }
            else
            {
                msu_process.Exited += new EventHandler(ProcessExited_msu);
                msu_process.EnableRaisingEvents = true;
                notifyIcon1.Visible = true;
                notifyIcon1.Icon = Properties.Resources.mkbot_off;
                Run_msu("/c");
            }

            bool autoconnect = false;
            if (configjson["connectOnStart"] != null)
            {
                autoconnect = (bool)configjson["connectOnStart"];
            }

            if (autoconnect)
            {
                notifyIcon1_MouseClick(new object(), new MouseEventArgs(MouseButtons.Left, 1, 1, 1, 1));
            }
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
                    var random = new Random();
                    if ((!can_update) && (random.Next(1, 3) == 1))
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
            Process.Start(UserDataPath + "\\config.json");
        }

        private void Click_MGCert(object source, EventArgs e)
        {
            Process.Start(UserDataPath + "\\mgcert.json");
        }

        private void Click_Extensions(object sender, EventArgs e)
        {
            Process.Start(UserDataPath + "\\extensions.json");
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
                Run_msu("/c");
            }
        }

        private void Click_info(object sender, EventArgs e)
        {
            if (Infowin.Visible)
            {
                Infowin.Activate();
            }
            else
            {
                Infowin.ShowDialog();
            }
        }

        private void Click_Exit(object source, EventArgs e)
        {
            notifyIcon1.Visible = false;
            if (online)
            {
                app_process.Kill();
            }
            if (can_update)
            {
                Run_setup(false);
            }
            Environment.Exit(0);
        }

        private void ShowToast(string title, string text, string type="action=None")
        {
            ToastContent toastContent = new ToastContent()
            {
                // Arguments when the user taps body of toast
                Launch = type,

                Visual = new ToastVisual()
                {
                    BindingGeneric = new ToastBindingGeneric()
                    {
                        Children =
                        {
                            new AdaptiveText()
                            {
                                Text = title,
                                HintMaxLines = 1
                            },
                            new AdaptiveText()
                            {
                                Text = text
                            }
                        },
                        AppLogoOverride = new ToastGenericAppLogo()
                        {
                            Source = DirectoryPath + "\\resources\\app\\MKBot_on.png",
                            HintCrop = ToastGenericAppLogoCrop.None
                        }
                    }
                }
            };

            // And create the toast notification
            var toast = new ToastNotification(toastContent.GetXml());
            toast.Activated += Toast_Activated;
            // And then show it
            DesktopNotificationManagerCompat.CreateToastNotifier().Show(toast);
        }

        private void ShowUpdateToast(string title = "Mulgyeol Software Update", string text = "Restart MK Bot to apply the latest update.", string type = "action=None")
        {
            ToastContent toastContent = new ToastContent()
            {
                // Arguments when the user taps body of toast
                Launch = type,

                Visual = new ToastVisual()
                {
                    BindingGeneric = new ToastBindingGeneric()
                    {
                        Children =
                        {
                            new AdaptiveText()
                            {
                                Text = title,
                                HintMaxLines = 1
                            },
                            new AdaptiveText()
                            {
                                Text = text
                            }
                        },
                        AppLogoOverride = new ToastGenericAppLogo()
                        {
                            Source = DirectoryPath + "\\resources\\app\\MKBot_install.png",
                            HintCrop = ToastGenericAppLogoCrop.None
                        }
                    }
                },
                Actions = new ToastActionsCustom()
                {
                    Buttons =
                    {
                        new ToastButton("Update Now", "action=install")
                        {
                            ActivationType = ToastActivationType.Foreground
                        },

                        new ToastButton("Later", "action=later")
                        {
                            ActivationType = ToastActivationType.Foreground
                        }
                    }
                }
            };

            // And create the toast notification
            var toast = new ToastNotification(toastContent.GetXml());
            toast.Activated += Toast_Activated;
            // And then show it
            DesktopNotificationManagerCompat.CreateToastNotifier().Show(toast);
        }

        //background
        private void Toast_Activated(ToastNotification sender, object arguments)
        {
            ToastActivatedEventArgs strArgs = arguments as ToastActivatedEventArgs;
            QueryString args = QueryString.Parse(strArgs.Arguments);

            switch (args["action"])
            {
                case "install":
                    Install_update();
                    break;
                case "openConfig":
                    Process.Start(UserDataPath + "\\config.json");
                    break;
                default:
                    Console.WriteLine("default");
                    break;
            }
        }

        private void Run_msu(string argv = "/c")
        {
            if (argv == "/c")
            {
                UpdateMenu.Enabled = false;
                UpdateMenu.Text = "Checking for Updates...";
            }
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

        private void Install_update()
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
        }

        private void Run_setup(bool autorun)
        {
            string param;
            if (autorun)
            {
                param = "/start /autorun";
            }
            else
            {
                param = "/start";
            }
            notifyIcon1.Visible = false;
            Process.Start("Update.exe", param);
            Environment.Exit(0);
        }

        private void ProcessExited_msu(object sender, EventArgs e)
        {
            if (msu_process.ExitCode == 0)
            {
                can_update = true;
                UpdateMenu.Enabled = true;
                UpdateMenu.Text = "Restart to Update";
                ShowUpdateToast();
                checking_update = false;
            }
            else if (msu_process.ExitCode == 1)
            {
                UpdateMenu.Enabled = true;
                UpdateMenu.Text = "Check for Updates...";

                if (checking_update)
                {
                    ShowToast("Mulgyeol Software Update", "There are currently no updates available.");
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
                ShowToast("An invalid token was provided.", "Review your settings for configured token.", "action=openConfig");
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
