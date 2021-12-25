import requests
from MGBotBuilder import VirtualCommandConsole
from mgylabs.utils.config import CONFIG

account_controller = VirtualCommandConsole()


@account_controller.command("/(generate|gen) <provider> <user> <pw>")
def generate(ctx, provider, user, pw):
    if provider == "mgylabs":
        r = requests.post(
            "https://mgylabs.herokuapp.com/auth/token",
            data={"username": user, "password": pw},
        )

        if r.status_code == 200:
            CONFIG.mgylabsToken = r.json()["refresh"]
            ctx.send("Success")
        else:
            ctx.send("Incorrect username or password.")
    else:
        ctx.send("This provider is not supported.")
