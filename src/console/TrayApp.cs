using Microsoft.QueryStringDotNET;
using Microsoft.Toolkit.Uwp.Notifications;
using Newtonsoft.Json.Linq;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows.Forms;
using Windows.UI.Notifications;

namespace MKBot
{
    class TrayApp : ApplicationContext
    {
        private NotifyIcon notifyIcon1;
        private ContextMenuStrip contextMenuStrip1;

        private bool manual_checking_update = false;
        private bool checking_update = false;
        private bool can_update = false;

        private ProcessStartInfo psi2 = new ProcessStartInfo();
        private Process msu_process = new Process();

        private System.Timers.Timer checkForTime = new System.Timers.Timer(30 * 1000);

        private ToolStripMenuItem UpdateMenu;
        private ToolStripMenuItem SwitchModeMenu;
        private Form Infowin;
        private Form Shellwin;

        private MKBotCoreManager MKBotCore;

        private string DirectoryPath;
        private string UserDataPath;
        private string[] args;

        private bool trayicon_middle_click_enabled = true;
        private bool CachedServerModeEnabled;
        private bool isTaskSchProcess = false;

        public TrayApp()
        {
#if DEBUG
            DirectoryPath = Path.GetFullPath(Environment.CurrentDirectory + "\\..");
#else
            DirectoryPath = Path.GetDirectoryName(Application.ExecutablePath);
#endif

            args = Environment.GetCommandLineArgs();
            if (args.Contains("--debug"))
            {
                UserDataPath = "data";
            }
            else
            {
                UserDataPath = Environment.GetEnvironmentVariable("LOCALAPPDATA") + $"\\Mulgyeol\\{Version.product_name}\\data";
            }

            if (args.Contains("--schtasks"))
            {
                isTaskSchProcess = true;
            }

            MKBotCore = new MKBotCoreManager(args.Contains("--debug"));
            MKBotCore.DiscordBotStarted += DiscordBot_Started;
            MKBotCore.DiscordBotExit += DiscordBot_Exit;

            var jsonString = File.ReadAllText(UserDataPath + "\\config.json");
            JObject configjson = JObject.Parse(jsonString);

            psi2.FileName = "bin\\msu.exe";
            psi2.WorkingDirectory = "bin";
            psi2.CreateNoWindow = true;
            psi2.UseShellExecute = false;
            msu_process.StartInfo = psi2;

            notifyIcon1 = new NotifyIcon();
            contextMenuStrip1 = new ContextMenuStrip();

            notifyIcon1.ContextMenuStrip = contextMenuStrip1;
            notifyIcon1.MouseClick += new MouseEventHandler(notifyIcon1_MouseClick);
            notifyIcon1.Text = Version.product_name;

            UpdateMenu = new ToolStripMenuItem("Check for Updates...", null, Click_Update);
            SwitchModeMenu = new ToolStripMenuItem("Switch to Server Mode", null, Click_Switch_Mode);

            contextMenuStrip1.Items.AddRange(new ToolStripItem[] {
                new ToolStripMenuItem("Settings", null, Click_Setting),
                new ToolStripMenuItem("MGCert", null, Click_MGCert),
                new ToolStripMenuItem("Extensions", null, Click_Extensions),
                SwitchModeMenu,
                new ToolStripSeparator(), UpdateMenu,
                new ToolStripMenuItem("About", null, Click_info),
                new ToolStripSeparator(),
                new ToolStripMenuItem("Exit", null, Click_Exit)
            });

            RenewServerModeEnabled();

            if (CachedServerModeEnabled && args.Contains("--post-update"))
            {
                isTaskSchProcess = true;
                Register_Task();
                Environment.Exit(0);
            }

            if (args.Contains("--switch-to-server"))
            {
                Register_Task();
                ShowToast("Changed to Server Mode.", "The Discord bot was started automatically.");
            }
            else if (args.Contains("--switch-to-desktop"))
            {
                Remove_Task();
                ShowToast("Changed to Desktop Mode.", "The Discord bot has been terminated.");
            }

            msu_process.Exited += new EventHandler(ProcessExited_msu);
            msu_process.EnableRaisingEvents = true;
            notifyIcon1.Visible = true;
            notifyIcon1.Icon = Properties.Resources.mkbot_off;

            bool auto_connect = false;
            if (configjson["connectOnStart"] != null)
            {
                auto_connect = (bool)configjson["connectOnStart"] || CachedServerModeEnabled;
            }

            Infowin = new InfoForm();
            Shellwin = new ShellForm(MKBotCore, auto_connect, !CachedServerModeEnabled || isTaskSchProcess);

            Update_Switch_Mode_Menu();

            if (!CachedServerModeEnabled || isTaskSchProcess)
            {
                checkForTime.Elapsed += new System.Timers.ElapsedEventHandler(checkForTime_Elapsed_At_Startup);
                checkForTime.Enabled = true;
            }
            else
            {
                UpdateMenu.Enabled = false;
            }
        }

        private void DiscordBot_Exit(object sender, MKBotCoreExitEventArgs e)
        {
            trayicon_middle_click_enabled = true;
            notifyIcon1.Icon = Properties.Resources.mkbot_off;

            if (can_update)
            {
                MKBotCore.Kill();
                Run_setup(true);
            }
            if (e.ExitCode == 1)
            {
                ShowToast("An invalid token was provided.", "Review your settings for configured token.", "action=openConfig");
            }
        }

        private void DiscordBot_Started(object sender, EventArgs e)
        {
            trayicon_middle_click_enabled = true;
            notifyIcon1.Icon = Properties.Resources.mkbot_on;
        }

        //UI
        private void notifyIcon1_MouseClick(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Left)
            {
                if (Shellwin.Visible)
                {
                    //Shellwin.Activate();
                    Shellwin.Hide();
                }
                else
                {
                    Shellwin.Show();
                }
            }
            else if (e.Button == MouseButtons.Middle)
            {
                if (trayicon_middle_click_enabled && (!CachedServerModeEnabled || isTaskSchProcess))
                {
                    trayicon_middle_click_enabled = false;
                    notifyIcon1.Icon = Properties.Resources.mkbot_intermediate;
                    ((ShellForm)this.Shellwin).Toggle_Discord_Bot_Button();
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

        private bool RenewServerModeEnabled()
        {
            var task = SchtasksUtils.GetTask(Version.schtask_name);
            CachedServerModeEnabled = task != null && task.Enabled;
            return CachedServerModeEnabled;
        }

        private void Update_Switch_Mode_Menu()
        {
            if (RenewServerModeEnabled())
            {
                SwitchModeMenu.Text = "Switch to Desktop Mode";
                UpdateMenu.Enabled = false;
                if (Shellwin != null)
                {
                    ((ShellForm)this.Shellwin).SetDiscordBotCheckBoxEnabled(false);
                }
                Trace.TraceInformation("ServerMode: On");
            }
            else
            {
                SwitchModeMenu.Text = "Switch to Server Mode";
                UpdateMenu.Enabled = true;
                if (Shellwin != null)
                {
                    ((ShellForm)this.Shellwin).SetDiscordBotCheckBoxEnabled(true);
                }
                Trace.TraceInformation("ServerMode: Off");
            }

            SwitchModeMenu.Enabled = true;
        }

        private void Register_Task(bool run = true)
        {
            SwitchModeMenu.Enabled = false;

            if (MKBotCore.discord_online)
            {
                MKBotCore.DisableDiscordBot();
            }

            var xml_string = SchtasksUtils.CreateScheduledTaskXml("Mulgyeol MK Bot Host Task", System.Security.Principal.WindowsIdentity.GetCurrent().Name, $"{Paths.ExePath}\\{Version.exe_name}", "--schtasks", Paths.ExePath);

            try
            {
                var rt = SchtasksUtils.RegisterTask(Version.schtask_name, xml_string);
                rt.Enabled = true;
                CachedServerModeEnabled = true;

                if (run)
                {
                    rt.Run(null);
                }
            }
            catch (Exception ex)
            {
                CachedServerModeEnabled = false;
                Trace.TraceError(ex.ToString());
            }
        }

        private void Remove_Task()
        {
            SwitchModeMenu.Enabled = false;

            if (SchtasksUtils.RemoveTask(Version.schtask_name))
            {
                CachedServerModeEnabled = false;
            }
            else
            {
                RenewServerModeEnabled();
            }
        }

        private void Click_Switch_Mode(object sender, EventArgs e)
        {
            SwitchModeMenu.Enabled = false;

            if (CachedServerModeEnabled)
            {
                if (Utils.IsAdministrator)
                {
                    Remove_Task();
                    Update_Switch_Mode_Menu();

                    ShowToast("Changed to Desktop Mode.", "The Discord bot has been terminated.");
                }
                else
                {
                    Process app_process = new Process();
                    app_process.StartInfo.FileName = Application.ExecutablePath;
                    app_process.StartInfo.WorkingDirectory = DirectoryPath;
                    app_process.StartInfo.Arguments = "--switch-to-desktop";
                    app_process.StartInfo.Verb = "runas";

                    app_process.Start();

                    Environment.Exit(0);
                }
            }
            else
            {
                if (Utils.IsAdministrator)
                {
                    Register_Task();
                    Update_Switch_Mode_Menu();

                    ShowToast("Changed to Server Mode.", "The Discord bot was started automatically.");
                }
                else
                {
                    Process app_process = new Process();
                    app_process.StartInfo.FileName = Application.ExecutablePath;
                    app_process.StartInfo.WorkingDirectory = DirectoryPath;
                    app_process.StartInfo.Arguments = "--switch-to-server";
                    app_process.StartInfo.Verb = "runas";

                    app_process.Start();

                    Environment.Exit(0);
                }
            }
        }

        private void Click_Update(object sender, EventArgs e)
        {
            if (can_update)
            {
                if (MKBotCore.discord_online)
                {
                    MKBotCore.DisableDiscordBot();
                }
                else
                {
                    Run_setup(true);
                }
            }
            else
            {
                UpdateMenu.Enabled = false;
                manual_checking_update = true;
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
            if (MKBotCore.discord_online)
            {
                MKBotCore.DisableDiscordBot();
            }
            if (can_update)
            {
                MKBotCore.Kill();
                Run_setup(false);
            }
            Environment.Exit(0);
        }

        private void ShowToast(string title, string text, string type = "action=None")
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
                            Source = DirectoryPath + "\\resources\\app\\mkbot.png",
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
                            Source = DirectoryPath + "\\resources\\app\\mkbot.png",
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

        private void checkForTime_Elapsed_At_Startup(object sender, System.Timers.ElapsedEventArgs e)
        {
            checkForTime.Enabled = false;
            checkForTime.Interval = 60 * 60 * 1000;

            CheckForUpdate();

            checkForTime.Elapsed -= new System.Timers.ElapsedEventHandler(checkForTime_Elapsed_At_Startup);
            checkForTime.Elapsed += new System.Timers.ElapsedEventHandler(checkForTime_Elapsed);
            checkForTime.Enabled = true;
        }

        private void checkForTime_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            if (can_update)
            {
                Install_update();
            }
            else
            {
                CheckForUpdate();
            }
        }

        private void CheckForUpdate()
        {
            if (!can_update)
            {
                Run_msu("/c /sch");
            }
        }

        private void Run_msu(string argv = "/c")
        {
            if (checking_update)
            {
                return;
            }

            checking_update = true;

            UpdateMenu.Enabled = false;
            UpdateMenu.Text = "Checking for Updates...";

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
                if (MKBotCore.discord_online)
                {
                    MKBotCore.DisableDiscordBot();
                }
                else
                {
                    MKBotCore.Kill();
                    Run_setup(true);
                }
            }
        }

        private void Run_setup(bool autorun)
        {
            var flag = File.ReadAllText("bin\\msu_update.flag");

            if (autorun)
            {
                if (File.Exists(flag))
                {
                    File.Delete(flag);
                }
            }

            notifyIcon1.Visible = false;
            Environment.Exit(0);
        }

        private void ProcessExited_msu(object sender, EventArgs e)
        {
            if (msu_process.ExitCode == 0)
            {
                Trace.TraceInformation("> msu exit: 0");

                UpdateMenu.Text = "Installing Update...";

                Utils.PollUntil("Update ready mutex is active", () => { return Utils.MutexIsActive($"{Version.mutex_name}-ready"); });

                can_update = true;
                if (!CachedServerModeEnabled)
                {
                    UpdateMenu.Enabled = true;
                }
                UpdateMenu.Text = "Restart to Update";

                if (!(manual_checking_update))
                {
                    Install_update();
                }
                else
                {
                    ShowUpdateToast();
                }

                manual_checking_update = false;
            }
            else if (msu_process.ExitCode == 1)
            {
                Trace.TraceInformation("> msu exit: 1");
                if (!CachedServerModeEnabled)
                {
                    UpdateMenu.Enabled = true;
                }
                UpdateMenu.Text = "Check for Updates...";

                if (manual_checking_update)
                {
                    ShowToast("Mulgyeol Software Update", "There are currently no updates available.");
                    manual_checking_update = false;
                }
            }

            checking_update = false;
        }

        internal void Application_Exit(object sender, EventArgs e)
        {
            AsyncListener.TerminateListener();
        }
    }
}
