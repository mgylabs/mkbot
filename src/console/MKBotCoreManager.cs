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
    public delegate void ClientReceiveCallback(string response);

    public class ReceiveStateObject
    {
        // Size of receive buffer.
        public const int BufferSize = 256;
        // Receive buffer.
        public byte[] buffer = new byte[BufferSize];
        // Received data string.
        public StringBuilder sb = new StringBuilder();

        public ClientReceiveCallback callback = null;

        public ManualResetEvent receiveDone =
            new ManualResetEvent(false);
    }

    public class SendStateObject
    {
        public ManualResetEvent sendDone =
            new ManualResetEvent(false);
    }

    public class AsyncClient
    {
        // The port number for the remote device.
        private static int port = 8979;

        // ManualResetEvent instances signal completion.
        private static ManualResetEvent connectDone =
            new ManualResetEvent(false);

        private static Socket client;
        private static ClientReceiveCallback last_callback;

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

        public static void StartClient(ClientReceiveCallback callback = null)
        {
            // Connect to a remote device.
            try
            {
                connectDone.Reset();
                // Create a TCP/IP socket.
                client = new Socket(AddressFamily.InterNetwork,
                    SocketType.Stream, ProtocolType.Tcp);

                // Connect to the remote endpoint.
                client.BeginConnect("localhost", port, new AsyncCallback(ConnectCallback), null);
                connectDone.WaitOne();

                // Receive the response from the remote device.
                if (callback == null)
                {
                    Receive(last_callback);
                }
                else
                {
                    last_callback = callback;
                    Receive(callback);
                }
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
            }
        }

        private static void ConnectCallback(IAsyncResult ar)
        {
            try
            {
                client.EndConnect(ar);

                Console.WriteLine("Socket connected to {0}",
                    client.RemoteEndPoint.ToString());

                // Signal that the connection has been made.
                connectDone.Set();

                // Complete the connection.
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                client.BeginConnect("localhost", port, new AsyncCallback(ConnectCallback), null);
            }
        }

        private static ManualResetEvent Receive(ClientReceiveCallback callback)
        {
            try
            {
                // Create the state object.
                ReceiveStateObject state = new ReceiveStateObject();
                state.callback = callback;

                // Begin receiving the data from the remote device.
                client.BeginReceive(state.buffer, 0, ReceiveStateObject.BufferSize, 0,
                    new AsyncCallback(ReceiveCallback), state);

                return state.receiveDone;
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                return new ReceiveStateObject().receiveDone;
            }
        }

        private static void ReceiveCallback(IAsyncResult ar)
        {
            try
            {
                // from the asynchronous state object.
                ReceiveStateObject state = (ReceiveStateObject)ar.AsyncState;

                // Read data from the remote device.
                int bytesRead = client.EndReceive(ar);
                Console.WriteLine("> Read: {0}", bytesRead);

                // There might be more data, so store the data received so far.
                state.sb.Append(Encoding.UTF8.GetString(state.buffer, 0, bytesRead));

                if (bytesRead > 0 && bytesRead == ReceiveStateObject.BufferSize)
                {
                    // Get the rest of the data.
                    client.BeginReceive(state.buffer, 0, ReceiveStateObject.BufferSize, 0,
                        new AsyncCallback(ReceiveCallback), state);
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
                if (!client.Connected)
                {
                    ReceiveStateObject state = (ReceiveStateObject)ar.AsyncState;
                    StartClient(state.callback);
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
                client.BeginSend(byteData, 0, byteData.Length, 0,
                    new AsyncCallback(SendCallback), state);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());

                if (!client.Connected)
                {
                    StartClient();
                    connectDone.WaitOne();
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
                int bytesSent = client.EndSend(ar);
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
#if !DEBUG
            make_app_process_args();
#endif

            app_process.StartInfo = psi1;
            app_process.EnableRaisingEvents = true;
            app_process.Exited += new EventHandler(ProcessExited_app);
#if !DEBUG
            app_process.Start();
#endif
            AsyncClient.StartClient(recv_callback);
        }

        private void make_app_process_args()
        {
            var random = new Random();
            var port = AsyncClient.GetAvailablePort(random.Next(2000, 49151));
            psi1.Arguments = "--port " + port.ToString();

            if (debug)
            {
                psi1.Arguments += "--debug";
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
                    OnMKBotCoreStarted(EventArgs.Empty);
                    break;
                case "disableDiscordBot":
                    discord_online = false;
                    MKBotCoreExitEventArgs eargs = new MKBotCoreExitEventArgs();
                    eargs.ExitCode = Int32.Parse(args["exitcode"]);
                    OnMKBotCoreExit(eargs);
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

        public void Run()
        {
            if (!discord_online)
            {
                AsyncClient.Send("action=enableDiscordBot");
            }
        }

        public void Kill()
        {
            if (discord_online)
            {
                AsyncClient.Send("action=disableDiscordBot");
            }
        }

        public void SendShellCommand(string data)
        {
            data = Uri.EscapeDataString(data);
            AsyncClient.Send("action=shell&request=" + data);
        }

        private void ProcessExited_app(object sender, EventArgs e)
        {
            make_app_process_args();

            app_process.Start();

            AsyncClient.StartClient(recv_callback);
        }

        protected virtual void OnMKBotCoreStarted(EventArgs e)
        {
            EventHandler handler = MKBotCoreStarted;
            if (handler != null)
            {
                handler(this, e);
            }
        }

        public event EventHandler MKBotCoreStarted;

        protected virtual void OnMKBotCoreExit(MKBotCoreExitEventArgs e)
        {
            EventHandler<MKBotCoreExitEventArgs> handler = MKBotCoreExit;
            if (handler != null)
            {
                handler(this, e);
            }
        }

        public event EventHandler<MKBotCoreExitEventArgs> MKBotCoreExit;

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
