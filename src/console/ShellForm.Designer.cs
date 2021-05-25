
namespace MKBot
{
    partial class ShellForm
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(ShellForm));
            this.discordCheckBox = new System.Windows.Forms.CheckBox();
            this.outputBox = new System.Windows.Forms.RichTextBox();
            this.userInputBox = new System.Windows.Forms.TextBox();
            this.sendButton = new System.Windows.Forms.Button();
            this.toggleButton = new System.Windows.Forms.CheckBox();
            this.SuspendLayout();
            //
            // discordCheckBox
            //
            this.discordCheckBox.AutoSize = true;
            this.discordCheckBox.Location = new System.Drawing.Point(21, 25);
            this.discordCheckBox.Name = "discordCheckBox";
            this.discordCheckBox.Size = new System.Drawing.Size(132, 16);
            this.discordCheckBox.TabIndex = 0;
            this.discordCheckBox.Text = "Enable Discord Bot";
            this.discordCheckBox.UseVisualStyleBackColor = true;
            this.discordCheckBox.Click += new System.EventHandler(this.discordCheckBox_Click);
            //
            // outputBox
            //
            this.outputBox.BackColor = System.Drawing.SystemColors.Window;
            this.outputBox.Location = new System.Drawing.Point(12, 62);
            this.outputBox.Name = "outputBox";
            this.outputBox.ReadOnly = true;
            this.outputBox.ScrollBars = System.Windows.Forms.RichTextBoxScrollBars.Vertical;
            this.outputBox.Size = new System.Drawing.Size(469, 180);
            this.outputBox.TabIndex = 1;
            this.outputBox.Text = "";
            this.outputBox.TextChanged += new System.EventHandler(this.outputBox_TextChanged);
            //
            // userInputBox
            //
            this.userInputBox.Location = new System.Drawing.Point(12, 257);
            this.userInputBox.Name = "userInputBox";
            this.userInputBox.Size = new System.Drawing.Size(388, 21);
            this.userInputBox.TabIndex = 2;
            //
            // sendButton
            //
            this.sendButton.Location = new System.Drawing.Point(406, 257);
            this.sendButton.Name = "sendButton";
            this.sendButton.Size = new System.Drawing.Size(75, 23);
            this.sendButton.TabIndex = 3;
            this.sendButton.Text = "Send";
            this.sendButton.UseVisualStyleBackColor = true;
            this.sendButton.Click += new System.EventHandler(this.sendButton_Click);
            //
            // toggleButton
            //
            this.toggleButton.Appearance = System.Windows.Forms.Appearance.Button;
            this.toggleButton.Location = new System.Drawing.Point(375, 21);
            this.toggleButton.Name = "toggleButton";
            this.toggleButton.Size = new System.Drawing.Size(99, 22);
            this.toggleButton.TabIndex = 4;
            this.toggleButton.Text = "Expand Shell";
            this.toggleButton.TextAlign = System.Drawing.ContentAlignment.MiddleCenter;
            this.toggleButton.UseVisualStyleBackColor = true;
            this.toggleButton.CheckedChanged += new System.EventHandler(this.toggleButton_CheckedChanged);
            //
            // ShellForm
            //
            this.AcceptButton = this.sendButton;
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(494, 291);
            this.Controls.Add(this.toggleButton);
            this.Controls.Add(this.sendButton);
            this.Controls.Add(this.userInputBox);
            this.Controls.Add(this.outputBox);
            this.Controls.Add(this.discordCheckBox);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "ShellForm";
            this.ShowInTaskbar = false;
            this.StartPosition = System.Windows.Forms.FormStartPosition.Manual;
            this.Text = "Mulgyeol MK Bot Shell";
            this.TopMost = true;
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.ShellForm_FormClosing);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.CheckBox discordCheckBox;
        private System.Windows.Forms.RichTextBox outputBox;
        private System.Windows.Forms.TextBox userInputBox;
        private System.Windows.Forms.Button sendButton;
        private System.Windows.Forms.CheckBox toggleButton;
    }
}
