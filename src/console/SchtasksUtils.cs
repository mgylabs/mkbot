using System;
using System.Diagnostics;
using TaskScheduler;

namespace MKBot
{
    class SchtasksUtils
    {
        private static TaskScheduler.TaskScheduler ts = new TaskScheduler.TaskScheduler();

        static SchtasksUtils()
        {
            ts.Connect();
        }

        public enum TaskCreation
        {
            Create = 2,
            CreateOrUpdate = 6,
            Disable = 8,
            DontAddPrincipalAce = 0x10,
            IgnoreRegistrationTriggers = 0x20,
            Update = 4,
            ValidateOnly = 1
        }

        public static string MultiLine(params string[] args)
        {
            return string.Join(Environment.NewLine, args);
        }

        public static IRegisteredTask GetTask(string path)
        {
            ITaskFolder tf = ts.GetFolder("\\");

            try
            {
                return tf.GetTask(path);
            }
            catch (Exception ex)
            {
                Trace.TraceError(ex.ToString());
                return null;
            }
        }

        public static void ChangeTaskEnabled(string path, bool enabled)
        {
            ITaskFolder tf = ts.GetFolder("\\");
            var rt = tf.GetTask(path);
            rt.Enabled = enabled;
        }

        public static bool RemoveTask(string path)
        {
            ITaskFolder tf = ts.GetFolder("\\");

            try
            {
                var rt = tf.GetTask(path);
                rt.Stop(0);

                tf.DeleteTask(path, 0);
                return true;
            }
            catch (Exception ex)
            {
                Trace.TraceError(ex.ToString());
                return false;
            }
        }

        public static bool TaskExists(string path)
        {
            if (GetTask(path) != null)
            {
                return true;
            }

            return false;
        }

        public static IRegisteredTask RegisterTask(string path, string xml, TaskCreation createType = TaskCreation.CreateOrUpdate, string userId = null, string password = null, _TASK_LOGON_TYPE logonType = _TASK_LOGON_TYPE.TASK_LOGON_S4U, string sddl = null)
        {
            ITaskFolder tf = ts.GetFolder("\\");
            var rt = tf.RegisterTask(path, xml, (int)createType, userId, password, logonType, sddl);
            return rt;
        }

        public static string CreateScheduledTaskXml(string description, string userId, string command, string args, string workingDir)
        {
            return MultiLine("<?xml version=\"1.0\" encoding=\"UTF-16\"?>",
                    "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\">",
                    "    <RegistrationInfo>",
                    $"     <Description>{description}</Description>",
                    "    </RegistrationInfo>",
                    "    <Triggers>",
                    "    <BootTrigger>",
                    "        <Enabled>true</Enabled>",
                    "    </BootTrigger>",
                    "    </Triggers>",
                    "    <Principals>",
                    "    <Principal id=\"Author\">",
                    $"        <UserId>{userId}</UserId>",
                    "        <LogonType>S4U</LogonType>",
                    "        <RunLevel>HighestAvailable</RunLevel>",
                    "    </Principal>",
                    "    </Principals>",
                    "    <Settings>",
                    "    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>",
                    "    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>",
                    "    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>",
                    "    <AllowHardTerminate>true</AllowHardTerminate>",
                    "    <StartWhenAvailable>true</StartWhenAvailable>",
                    "    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>",
                    "    <IdleSettings>",
                    "        <StopOnIdleEnd>true</StopOnIdleEnd>",
                    "        <RestartOnIdle>false</RestartOnIdle>",
                    "    </IdleSettings>",
                    "    <AllowStartOnDemand>true</AllowStartOnDemand>",
                    "    <Enabled>true</Enabled>",
                    "    <Hidden>false</Hidden>",
                    "    <RunOnlyIfIdle>false</RunOnlyIfIdle>",
                    "    <WakeToRun>false</WakeToRun>",
                    "    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>",
                    "    <Priority>4</Priority>",
                    "    </Settings>",
                    "    <Actions Context=\"Author\">",
                    "    <Exec>",
                    $"        <Command>{command}</Command>",
                    $"        <Arguments>{args}</Arguments>",
                    $"        <WorkingDirectory>{workingDir}</WorkingDirectory>",
                    "    </Exec>",
                    "    </Actions>",
                    "</Task>"
                );
        }
    }
}
