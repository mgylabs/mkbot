using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace MKBot
{
    class Version
    {
        public static bool stable = false;
        public static bool canary = false;
        public static string version_type;
        public static string version_str;
        public static string commit;
        public static string mutex_name;
        public static string product_name;

        static public void load_version_info()
        {
            var jsonString = File.ReadAllText("info\\version.json");
            JObject json = JObject.Parse(jsonString);

            string[] version_array = json["version"].ToString().Split('-');
            commit = json["commit"].ToString();
            version_str = version_array[0];

            if (version_array.Length > 1 && version_array[1] == "beta")
            {
                version_type = "Canary";
                canary = true;
                mutex_name = "MKBotCanary";
                product_name = "Mulgyeol MK Bot Canary";
            }
            else
            {
                version_type = "Stable";
                stable = true;
                mutex_name = "MKBot";
                product_name = "Mulgyeol MK Bot";
            }
        }
    }
}
