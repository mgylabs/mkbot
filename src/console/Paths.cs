using System;
using System.Linq;

namespace MKBot
{
    class Paths
    {
        public static string UserDataPath;
        public static string LocalAppDataPath = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        public static string ExePath = LocalAppDataPath + $"\\Programs\\{Version.product_name}";

        static public void load_paths_info()
        {
            var args = Environment.GetCommandLineArgs();
            if (args.Contains("--debug"))
            {
                UserDataPath = "data";
            }
            else
            {
                UserDataPath = LocalAppDataPath + $"\\Mulgyeol\\{Version.product_name}\\data";
            }
        }
    }
}
