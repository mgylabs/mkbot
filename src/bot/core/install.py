from discord.ext import commands
import discord
from .utils.config import CONFIG, add_data
from .utils import api
from mulgyeol_oauth.InstalledAppFlow import InstalledAppFlow  # pylint: disable=import-error
import requests
import os
import zipfile
import shutil


def setup(bot: commands.Bot):
    @commands.command()
    @bot.MGCert.verify(1)
    async def install(ctx: commands.Context, ext_id: str, option=None):
        """
        Install extensions (Requires Admin Permission)

        Usage:
        - install
        {commandPrefix}install name
        - update
        {commandPrefix}install name -U
        """
        name = ext_id.replace('-', '_')
        ext_data = api.find_available_extension(name)
        cur_commit = api.load_commit(name)

        if ext_data == None:
            await ctx.send(embed=bot.replyformat.get(ctx, f"{ext_id} 확장을 찾을 수 없습니다."))
            return

        base_url = 'https://gitlab.com/api/v4'
        req_headers = {}

        if ext_data.get('auth', False):
            if len(CONFIG.gitlabToken) == 0:
                flow = InstalledAppFlow(**api.get_gitlab_oauth())
                credentials = flow.run_local_server()
                add_data('gitlabToken', credentials['access_token'])
                CONFIG.gitlabToken = credentials['access_token']
                req_headers = {
                    'Authorization': 'Bearer ' + CONFIG.gitlabToken}
            else:
                req_headers = {
                    'Authorization': 'Bearer ' + CONFIG.gitlabToken}

        last_commit = requests.get(
            f"{base_url}/projects/{ext_data['project_id']}/repository/commits/HEAD", headers=req_headers, params={'ref_name': 'master'}).json()['id']

        if (cur_commit == None) or ((option == '-U') and (cur_commit != last_commit)):

            download_file_name = os.getenv(
                'TEMP') + f'\\mkbot-update\\{name}.zip'

            os.makedirs(os.path.dirname(download_file_name), exist_ok=True)

            res = requests.get(
                f"{base_url}/projects/{ext_data['project_id']}/jobs/artifacts/master/download?job=release", headers=req_headers)

            with open(download_file_name, 'wb') as f:
                f.write(res.content)

            _zip = zipfile.ZipFile(download_file_name)
            _zip.extractall(api.extensions_path)

            if os.path.isdir(f"{api.extensions_path}\\{name}"):
                shutil.rmtree(f"{api.extensions_path}\\{name}")
            shutil.move(
                f"{api.extensions_path}\\{name.replace('_', '-')}-master-{last_commit}", f"{api.extensions_path}\\{name}")

            api.save_commit(name, last_commit)
            api.set_enabled(name)

            await ctx.send(embed=bot.replyformat.get(ctx, f"{ext_id} 확장 설치가 완료되었습니다.", "확장을 적용하려면 MK Bot을(를) 다시 시작하세요."))
        elif (option == '-U'):
            await ctx.send(embed=bot.replyformat.get(ctx, "사용 가능한 업데이트가 없습니다.", f"**{ext_id}**\n{last_commit[:8]}"))
        else:
            await ctx.send(embed=bot.replyformat.get(ctx, "이미 설치된 확장입니다.", f"`{ctx.message.content} -U` 을(를) 시도해 보세요."))

    bot.add_command(install)
