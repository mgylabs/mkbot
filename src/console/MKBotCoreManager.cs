using Microsoft.QueryStringDotNET;
using System;
using System.Diagnostics;
using System.Linq;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace MKBot
{
    public delegate void ListenerReceiveCallback(string response);

    public class StateObject
    {
        // Size of receive buffer.
        public const int BufferSize = 256;
        // Receive buffer.
        public byte[] buffer = new byte[BufferSize];
        // Received data string.
        public StringBuilder sb = new StringBuilder();

        public ListenerReceiveCallback callback = null;

        public ManualResetEvent receiveDone =
            new ManualResetEvent(false);
    }

    public class SendStateObject
    {
        public ManualResetEvent sendDone =
            new ManualResetEvent(false);
    }

    public class AsyncListener
    {
        // The port number for the remote device.
        private static int port = 8979;

        // ManualResetEvent instances signal completion.
        private static ManualResetEvent connectDone =
            new ManualResetEvent(false);

        //private static Socket listener;
        private static Socket listener;
        private static Socket handler;
        private static ListenerReceiveCallback last_callback;

        public static int GetAvailablePort(int startingPort)
        {
            var properties = IPGlobalProperties.GetIPGlobalProperties();

            //getting active connections
            var tcpConnectionPorts = properties.GetActiveTcpConnections()
                                .Where(n => n.LocalEndPoint.Port >= startingPort)
                                .Select(n => n.LocalEndPoint.Port);

            //getting active tcp listners - WCF service listening in tcp
            var tcpListenerPorts = properties.GetActiveTcpListeners()
                                .Where(n => n.Port >= startingPort)
                                .Select(n => n.Port);

            //getting active udp listeners
            var udpListenerPorts = properties.GetActiveUdpListeners()
                                .Where(n => n.Port >= startingPort)
                                .Select(n => n.Port);

            port = Enumerable.Range(startingPort, ushort.MaxValue)
                .Where(i => !tcpConnectionPorts.Contains(i))
                .Where(i => !tcpListenerPorts.Contains(i))
                .Where(i => !udpListenerPorts.Contains(i))
                .FirstOrDefault();

            Console.WriteLine("Assigned port: {0}", port);

            return port;
        }

        public static void StartListener(ListenerReceiveCallback callback = null)
        {
            // Connect to a remote device.
            IPEndPoint localEndPoint = new IPEndPoint(IPAddress.Parse("127.0.0.1"), port);

            // Create a TCP/IP socket.
            listener = new Socket(AddressFamily.InterNetwork,
                SocketType.Stream, ProtocolType.Tcp);

            listener.Bind(localEndPoint);
            listener.Listen(1);

            BeginAccept(callback);
        }

        private static void BeginAccept(ListenerReceiveCallback callback, bool wait=false)
        {
            connectDone.Reset();

            Console.WriteLine("Waiting for a connection...");

            StateObject state = new StateObject();
            state.callback = callback;
            last_callback = callback;
            listener.BeginAccept(new AsyncCallback(AcceptCallback), state);

            if (wait)
            {
                connectDone.WaitOne();
            }
        }

        public static void WaitBeginAccept()
        {
            connectDone.WaitOne();
        }

        public static void TerminateListener()
        {
            handler.Shutdown(SocketShutdown.Both);
            handler.Close();
        }

        private static ManualResetEvent Receive(ListenerReceiveCallback callback)
        {
            try
            {
                // Create the state object.
                StateObject state = new StateObject();
                state.callback = callback;

                // Begin receiving the data from the remote device.
                handler.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0,
                    new AsyncCallback(ReadCallback), state);

                return state.receiveDone;
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                return new StateObject().receiveDone;
            }
        }

        private static void AcceptCallback(IAsyncResult ar)
        {
            connectDone.Set();

            StateObject state = (StateObject)ar.AsyncState;
            handler = listener.EndAccept(ar);

            Receive(state.callback);
        }

        private static void ReadCallback(IAsyncResult ar)
        {
            // from the asynchronous state object.
            StateObject state = (StateObject)ar.AsyncState;

            try
            {
                // Read data from the remote device.
                int bytesRead = handler.EndReceive(ar);
                Console.WriteLine("> Read: {0}", bytesRead);

                // There might be more data, so store the data received so far.
                state.sb.Append(Encoding.UTF8.GetString(state.buffer, 0, bytesRead));

                if (bytesRead > 0 && bytesRead == StateObject.BufferSize)
                {
                    // Get the rest of the data.
                    handler.BeginReceive(state.buffer, 0, StateObject.BufferSize, 0,
                        new AsyncCallback(ReadCallback), state);
                }
                else
                {
                    // All the data has arrived; put it in response.
                    if (state.sb.Length > 1)
                    {
                        state.callback(state.sb.ToString());
                    }
                    // Signal that all bytes have been received.
                    state.receiveDone.Set();

                    Receive(state.callback);
                }
            }
            catch (Exception e)
            {
                Console.WriteLine("Recv Callback Error: " + e.ToString());
                if (!handler.Connected)
                {
                    BeginAccept(state.callback, true);
                }
            }
        }

        public static void Send(String data)
        {
            try
            {
                SendStateObject state = new SendStateObject();

                // Convert the string data to byte data using ASCII encoding.
                byte[] byteData = Encoding.ASCII.GetBytes(data);

                // Begin sending the data to the remote device.
                handler.BeginSend(byteData, 0, byteData.Length, 0,
                    new AsyncCallback(SendCallback), state);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());

                if (!handler.Connected)
                {
                    BeginAccept(last_callback, true);
                    Send(data);
                }
            }

        }

        private static void SendCallback(IAsyncResult ar)
        {
            try
            {
                // Retrieve the socket from the state object.
                SendStateObject state = (SendStateObject)ar.AsyncState;

                // Complete sending the data to the remote device.
                int bytesSent = handler.EndSend(ar);
                Console.WriteLine("Sent {0} bytes to server.", bytesSent);

                // Signal that all bytes have been sent.
                state.sendDone.Set();
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
        }
    }

    public class MKBotCoreManager
    {
        private ProcessStartInfo psi1 = new ProcessStartInfo();
        private Process app_process = new Process();

        public bool discord_online = false;
        private bool debug;

        public MKBotCoreManager(bool debug)
        {
            this.debug = debug;

            psi1.FileName = "bin\\MKBotCore.exe";
            psi1.WorkingDirectory = "bin";
            psi1.CreateNoWindow = true;
            psi1.UseShellExecute = false;
            app_process.StartInfo = psi1;
            app_process.EnableRaisingEvents = true;
            app_process.Exited += new EventHandler(ProcessExited_app);

            Utils.retry("Start Listener", (attempt) => {
#if !DEBUG
                make_app_process_args();
#endif
                AsyncListener.StartListener(recv_callback);
            });

#if !DEBUG
            app_process.Start();
#endif

            AsyncListener.WaitBeginAccept();
        }

        private void make_app_process_args()
        {
            var random = new Random();
            var port = AsyncListener.GetAvailablePort(random.Next(2000, 49151));
            app_process.StartInfo.Arguments = "--port " + port.ToString();

            if (debug)
            {
                app_process.StartInfo.Arguments += " --debug";
            }
        }

        private void recv_callback(string data)
        {
            Console.WriteLine("Recv Data: {0}", data);
            QueryString args = QueryString.Parse(data);

            if (!args.Contains("action"))
            {
                return;
            }

            switch (args["action"])
            {
                case "enableDiscordBot":
                    discord_online = true;
                    OnDiscordBotStarted(EventArgs.Empty);
                    break;
                case "disableDiscordBot":
                    discord_online = false;
                    MKBotCoreExitEventArgs eargs = new MKBotCoreExitEventArgs();
                    eargs.ExitCode = Int32.Parse(args["exitcode"]);
                    OnDiscordBotExit(eargs);
                    break;
                case "shell":
                    MKBotCoreShellResponseEventArgs sargs = new MKBotCoreShellResponseEventArgs();
                    sargs.response = Uri.UnescapeDataString(args["response"]);
                    OnMKBotCoreShellResponse(sargs);
                    break;
                default:
                    break;
            }
        }

        public void Kill()
        {
            try
            {
                if (!app_process.HasExited)
                {
                    app_process.Kill();
                }
            }
            catch (Exception)
            {
                Console.WriteLine("Kill MKBotCore");
            }
        }

        public void EnableDiscordBot()
        {
            if (!discord_online)
            {
                AsyncListener.Send("action=enableDiscordBot");
            }
        }

        public void DisableDiscordBot()
        {
            if (discord_online)
            {
                AsyncListener.Send("action=disableDiscordBot");
            }
        }

        public void SendShellCommand(string data)
        {
            EnsureProcessRunning();

            data = Uri.EscapeDataString(data);
            AsyncListener.Send("action=shell&request=" + data);
        }

        private void ProcessExited_app(object sender, EventArgs e)
        {
            Console.WriteLine("MKBotCore was exited.");

            MKBotCoreExitEventArgs eargs = new MKBotCoreExitEventArgs();
            eargs.ExitCode = 1234;
        }

        private void EnsureProcessRunning()
        {
            try
            {
                if (app_process.HasExited)
                {
                    make_app_process_args();
                    app_process.Start();

                    Console.WriteLine("MKBotCore was started.");
                }
            }
            catch (Exception)
            {

            }
        }

        protected virtual void OnDiscordBotStarted(EventArgs e)
        {
            EventHandler handler = DiscordBotStarted;
            if (handler != null)
            {
                handler(this, e);
            }
        }

        public event EventHandler DiscordBotStarted;

        protected virtual void OnDiscordBotExit(MKBotCoreExitEventArgs e)
        {
            EventHandler<MKBotCoreExitEventArgs> handler = DiscordBotExit;
            if (handler != null)
            {
                handler(this, e);
            }
        }

        public event EventHandler<MKBotCoreExitEventArgs> DiscordBotExit;

        protected virtual void OnMKBotCoreShellResponse(MKBotCoreShellResponseEventArgs e)
        {
            EventHandler<MKBotCoreShellResponseEventArgs> handler = MKBotCoreShellResponse;
            if (handler != null)
            {
                handler(this, e);
            }
        }

        public event EventHandler<MKBotCoreShellResponseEventArgs> MKBotCoreShellResponse;
    }

    public class MKBotCoreExitEventArgs : EventArgs
    {
        public int ExitCode { get; set; }
    }

    public class MKBotCoreShellResponseEventArgs : EventArgs
    {
        public string response { get; set; }
    }
}
