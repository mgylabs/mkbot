using Microsoft.Toolkit.Uwp.Notifications;
using System;
using System.Runtime.InteropServices;

namespace MKBot
{
    [ClassInterface(ClassInterfaceType.None)]
    [ComSourceInterfaces(typeof(INotificationActivationCallback))]
    [Guid("3f7eb835-ef29-45f5-acb5-a078d127dc94"), ComVisible(true)]
    public class MyNotificationActivator : NotificationActivator
    {
        public override void OnActivated(string invokedArgs, NotificationUserInput userInput, string appUserModelId)
        {
            Console.WriteLine("onActivated");
        }
    }
}
