﻿using Newtonsoft.Json.Linq;
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
            try
            {
                var jsonString = File.ReadAllText("info\\version.json");
                JObject json = JObject.Parse(jsonString);

                string[] version_array = json["version"].ToString().Split('-');
                string commit = json["commit"].ToString();
                string version_str = version_array[0];
                if (version_array.Length > 1 && version_array[1] == "dev")
                {
                    version_str += " Canary";
                }
                else
                {
                    version_str += " Stable";
                }
                label1.Text = "Version " + version_str + "\nCommit " + commit + "\n\nCopyright © 2020 Mulgyeol Labs. All rights reserved.";
            }
            catch
            {
                label1.Text = "Mulgyeol MK Bot\nTest Mode \nCopyright © 2020 Mulgyeol Labs. All rights reserved.";
            }
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
            Process.Start("https://github.com/mgylabs/mulgyeol-mkbot/releases");
        }

        private void linkLabel2_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            Process.Start("https://github.com/mgylabs/mulgyeol-mkbot/issues");
        }
    }
}