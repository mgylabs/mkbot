using Newtonsoft.Json.Linq;
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace MKBot
{
    public partial class InfoForm : Form
    {
        public InfoForm()
        {
            InitializeComponent();
            button1.Select();
            var jsonString = File.ReadAllText("info\\version.json");
            JObject json = JObject.Parse(jsonString);
            label1.Text = "Mulgyeol MK Bot\nVersion "+json["version"]+"\nCopyright © 2020 Mulgyeol Labs. All Rights Reserved.";
        }

        private void button1_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        private void InfoForm_HelpButtonClicked(object sender, CancelEventArgs e)
        {
            Process.Start("https://gitlab.com/mgylabs/mulgyeol-mkbot/-/wikis/home");
        }

        private void linkLabel1_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            Process.Start("https://gitlab.com/mgylabs/mulgyeol-mkbot/-/releases");
        }

        private void linkLabel2_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            Process.Start("https://gitlab.com/mgylabs/mulgyeol-mkbot/-/issues");
        }
    }
}