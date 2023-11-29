using MKBot.Diagnostics;
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Security.Principal;
using System.Threading.Tasks;

namespace MKBot
{
    public delegate void FunctionPointer(int attempt);

    class Utils
    {
        public static string log_file_path;
        public static bool IsAdministrator => new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator);

        public static void retry(string task, FunctionPointer f, int max_attempts = 10)
        {
            int attempt = 0;

            while (true)
            {
                if (attempt >= max_attempts)
                {
                    throw new Exception($"There was an error while {task}! Please verify there are no processes still executing.");
                }

                attempt += 1;

                try
                {
                    f(attempt);
                    return;
                }
                catch (Exception ex)
                {
                    Trace.TraceError(ex.ToString());
                }

                Task.Delay(500).Wait();
            }
        }

        public static void init_log_file()
        {
            log_file_path = $"{Paths.UserDataPath}\\logs\\console\\console-{DateTimeOffset.Now.ToUnixTimeSeconds()}.log";

            Directory.CreateDirectory(Path.GetDirectoryName(log_file_path));

            Trace.Listeners.Add(new DateTimeConsoleTraceListener());
            Trace.Listeners.Add(new DateTimeTextWriterTraceListener(log_file_path));
            Trace.AutoFlush = true;

            Trace.TraceInformation($"{Version.product_name} Console");

            delete_old_log_file(20);
        }

        public static void delete_old_log_file(int max_log_file_count)
        {
            FileInfo[] all_log_files = new DirectoryInfo(Path.GetDirectoryName(log_file_path)).GetFiles("console*", SearchOption.TopDirectoryOnly).OrderBy(x => x.CreationTime).ToArray();

            Trace.TraceInformation($"Find {all_log_files.Length} log file(s)");

            if (all_log_files.Length > max_log_file_count)
            {
                all_log_files = all_log_files.Take(all_log_files.Length - max_log_file_count).ToArray();

                foreach (var log_file in all_log_files)
                {
                    try
                    {
                        Trace.TraceInformation($"Delete: {log_file.FullName}");
                        log_file.Delete();
                    }
                    catch (Exception ex)
                    {
                        Trace.TraceError($"Failed to delete {log_file.FullName}: {ex}");
                    }
                }
            }
        }

    }
}
