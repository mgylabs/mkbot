using System;
using System.Drawing;
using System.Windows.Forms;

namespace MKBot
{
    public partial class ShellForm : Form
    {
        private MKBotCoreManager MKBotCore;
        private delegate void SafeCallDelegate(bool status, bool enabled);
        private delegate void SafeAppendDelegate(string data, bool enabled);


        public ShellForm(MKBotCoreManager MKBotCore, bool auto_connect, bool canToggleBot)
        {
            InitializeComponent();

            Icon = Properties.Resources.mkbot;

            outputBox.Hide();
            this.Size = new Size(510, 100);

            Update_location();

            this.MKBotCore = MKBotCore;

            this.discordCheckBox.Checked = MKBotCore.discord_online;

            MKBotCore.DiscordBotStarted += DiscordBot_Started;
            MKBotCore.DiscordBotExit += DiscordBot_Exit;
            MKBotCore.MKBotCoreShellResponse += MKBotCore_Shell_Response;

            if (canToggleBot)
            {
                if (auto_connect)
                {
                    discordCheckBox.Enabled = false;
                    discordCheckBox.Checked = true;

                    MKBotCore.EnableDiscordBot();
                }
            }
            else
            {
                discordCheckBox.Enabled = false;
            }
        }

        public void Toggle_Discord_Bot_Button()
        {
            discordCheckBox.Checked = !discordCheckBox.Checked;
            DiscordCheckBox_Click(new object(), new EventArgs());
        }

        private void MKBotCore_Shell_Response(object sender, MKBotCoreShellResponseEventArgs e)
        {
            var text = "MK Bot: " + e.response;

            if (outputBox.InvokeRequired)
            {
                outputBox.Invoke(new SafeAppendDelegate(Append_to_outputBox), text, true);
            }
            else
            {
                Append_to_outputBox(text, true);
            }
        }

        private void Append_to_outputBox(string data, bool buttonEanble = false)
        {
            outputBox.SelectionCharOffset = 8;
            outputBox.AppendText(data + "\n");
            if (buttonEanble)
            {
                this.sendButton.Enabled = true;
            }
        }

        private void DiscordBot_Exit(object sender, MKBotCoreExitEventArgs e)
        {
            SetDiscordBotCheckedSafe(false);
        }

        private void DiscordBot_Started(object sender, EventArgs e)
        {
            SetDiscordBotCheckedSafe(true);
        }

        private void SetDiscordBotCheckedSafe(bool status, bool enabled = true)
        {
            if (discordCheckBox.InvokeRequired)
            {
                discordCheckBox.Invoke(new SafeCallDelegate(SetDiscordBotChecked), status, enabled);
            }
            else
            {
                SetDiscordBotChecked(status, enabled);
            }
        }

        private void SetDiscordBotChecked(bool status, bool enabled = true)
        {
            discordCheckBox.Checked = status;
            discordCheckBox.Enabled = enabled;
        }

        public void SetDiscordBotCheckBoxEnabled(bool enabled)
        {
            discordCheckBox.Enabled = enabled;
        }

        private void toggleButton_CheckedChanged(object sender, EventArgs e)
        {
            if (this.toggleButton.Checked)
            {
                outputBox.Show();
                this.Size = new Size(510, 330);
                this.toggleButton.Text = "Collapse Shell";
            }
            else
            {
                this.Size = new Size(510, 100);
                outputBox.Hide();
                this.toggleButton.Text = "Expand Shell";
            }

            Update_location();
        }

        private void Update_location()
        {
            this.Location = new Point(Screen.PrimaryScreen.WorkingArea.Width - this.Width, Screen.PrimaryScreen.WorkingArea.Height - this.Height);
        }

        private void ShellForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            this.Hide();
            e.Cancel = true;
        }

        private void DiscordCheckBox_Click(object sender, EventArgs e)
        {
            discordCheckBox.Enabled = false;
            if (discordCheckBox.Checked)
            {
                MKBotCore.EnableDiscordBot();
            }
            else
            {
                MKBotCore.DisableDiscordBot();
            }
        }

        private void SendButton_Click(object sender, EventArgs e)
        {
            var text = userInputBox.Text;
            if (text.Length > 0)
            {
                userInputBox.Text = "";
                this.sendButton.Enabled = false;
                MKBotCore.SendShellCommand(text);
                Append_to_outputBox("User: " + text);
            }
        }

        private void OutputBox_TextChanged(object sender, EventArgs e)
        {
            outputBox.SelectionStart = outputBox.Text.Length;
            outputBox.ScrollToCaret();
        }
    }
}
