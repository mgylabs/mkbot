using Microsoft.Toolkit.Uwp.Notifications;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace MKBot
{
    static class Program
    {
        /// <summary>
        /// 해당 애플리케이션의 주 진입점입니다.
        /// </summary>
        [STAThread]
        static void Main()
        {
#if DEBUG
            Environment.CurrentDirectory = Path.GetFullPath(Environment.CurrentDirectory + "\\..") + "\\build";
#else
            Environment.CurrentDirectory = Path.GetDirectoryName(Application.ExecutablePath);
#endif
            Version.load_version_info();
            Paths.load_paths_info();
            Utils.init_log_file();

            Trace.TraceInformation($"CurrentDir: {Environment.CurrentDirectory}");

            bool createnew;

            try
            {
                using (Mutex mutex = new Mutex(true, Version.mutex_name, out createnew))
                {

                    if (!createnew)
                    {
                        MessageBox.Show("Mulgyeol MK Bot is already running.");

                        Trace.TraceInformation("Mulgyeol MK Bot is already running.");
                        return;
                    }

                    DesktopNotificationManagerCompat.RegisterAumidAndComServer<MyNotificationActivator>(Version.dname);
                    DesktopNotificationManagerCompat.RegisterActivator<MyNotificationActivator>();
                    Application.EnableVisualStyles();
                    Application.SetCompatibleTextRenderingDefault(false);
                    TrayApp app = new TrayApp();
                    Application.ApplicationExit += new EventHandler(app.Application_Exit);
                    Application.Run(app);
                }
            }
            catch (Exception ex)
            {
                Trace.TraceError(ex.ToString());
            }
        }
    }
}
