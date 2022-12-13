using System;
using System.Threading.Tasks;

namespace MKBot
{
    public delegate void FunctionPointer(int attempt);

    class Utils
    {
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
                    //Trace.TraceError(ex.ToString());
                    Console.WriteLine(ex.ToString());
                }

                Task.Delay(1000).Wait();
            }
        }
    }
}
