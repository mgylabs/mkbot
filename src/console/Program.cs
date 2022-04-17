using Microsoft.Toolkit.Uwp.Notifications;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
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
            Version.load_version_info();

            bool createnew;

            Mutex mutex = new Mutex(true, Version.mutex_name, out createnew);

            if (!createnew)
            {
                MessageBox.Show("Mulgyeol MK Bot is already running.");
                return;
            }
            DesktopNotificationManagerCompat.RegisterAumidAndComServer<MyNotificationActivator>("com.mgylabs.mkbot");
            DesktopNotificationManagerCompat.RegisterActivator<MyNotificationActivator>();
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            TrayApp app = new TrayApp();
            Application.ApplicationExit += new EventHandler(app.Application_Exit);
            Application.Run(app);
        }
    }
}
