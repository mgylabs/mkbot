using System;
using System.Drawing;
using System.Windows.Forms;

namespace MKBot
{
    public partial class ShellForm : Form
    {
        private MKBotCoreManager MKBotCore;
        private delegate void SafeCallDelegate(bool status, bool enabled);
        private delegate void SafeAppendDelegate(string data);


        public ShellForm(MKBotCoreManager MKBotCore)
        {
            InitializeComponent();

            this.Size = new Size(510, 100);

            update_location();

            this.MKBotCore = MKBotCore;

            this.discordCheckBox.Checked = MKBotCore.discord_online;

            MKBotCore.MKBotCoreStarted += MKBotCore_Started;
            MKBotCore.MKBotCoreExit += MKbotCore_Exit;
            MKBotCore.MKBotCoreShellResponse += MKBotCore_Shell_Response;
        }

        private void MKBotCore_Shell_Response(object sender, MKBotCoreShellResponseEventArgs e)
        {
            var text = "MK Bot: " + e.response;

            if (outputBox.InvokeRequired)
            {
                outputBox.Invoke(new SafeAppendDelegate(Append_to_outputBox), text);
            }
            else
            {
                Append_to_outputBox(text);
            }
        }

        private void Append_to_outputBox(string data)
        {
            outputBox.SelectionCharOffset = 8;
            outputBox.AppendText(data + "\n");
        }

        private void MKbotCore_Exit(object sender, MKBotCoreExitEventArgs e)
        {
            setDiscordBotCheckedSafe(false);
        }

        private void MKBotCore_Started(object sender, EventArgs e)
        {
            setDiscordBotCheckedSafe(true);
        }

        private void setDiscordBotCheckedSafe(bool status, bool enabled = true)
        {
            if (discordCheckBox.InvokeRequired)
            {
                discordCheckBox.Invoke(new SafeCallDelegate(setDiscordBotChecked), status, enabled);
            }
            else
            {
                discordCheckBox.Checked = status;
            }
        }

        private void setDiscordBotChecked(bool status, bool enabled = true)
        {
            discordCheckBox.Checked = status;
            discordCheckBox.Enabled = enabled;
        }

        private void toggleButton_CheckedChanged(object sender, EventArgs e)
        {
            if (this.toggleButton.Checked)
            {
                this.Size = new Size(510, 330);
                this.toggleButton.Text = "Collapse Shell";
            }
            else
            {
                this.Size = new Size(510, 100);
                this.toggleButton.Text = "Expand Shell";
            }

            update_location();
        }

        private void update_location()
        {
            this.Location = new Point(Screen.PrimaryScreen.WorkingArea.Width - this.Width, Screen.PrimaryScreen.WorkingArea.Height - this.Height);
        }

        private void ShellForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            this.Hide();
            e.Cancel = true;
        }

        private void discordCheckBox_Click(object sender, EventArgs e)
        {
            discordCheckBox.Enabled = false;
            if (discordCheckBox.Checked)
            {
                MKBotCore.Run();
            }
            else
            {
                MKBotCore.Kill();
            }
        }

        private void sendButton_Click(object sender, EventArgs e)
        {
            var text = userInputBox.Text;
            if (text.Length > 0)
            {
                userInputBox.Text = "";
                MKBotCore.SendShellCommand(text);
                Append_to_outputBox("User: " + text);
            }
        }

        private void outputBox_TextChanged(object sender, EventArgs e)
        {
            outputBox.SelectionStart = outputBox.Text.Length;
            outputBox.ScrollToCaret();
        }
    }
}
