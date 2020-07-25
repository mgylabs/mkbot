import json

with open('../data/config.json', 'rt', encoding='utf-8') as f:
    TOKEN = json.load(f)

sch_url = 'https://mgylabs.gitlab.io/discord-bot/config.schema'

if TOKEN.get('$schema', None) != sch_url:
    with open('../data/config.json', 'wt', encoding='utf-8') as f:
        if '$schema' in TOKEN:
            TOKEN['$schema'] = sch_url
            json.dump(TOKEN,
                      f, indent=4, ensure_ascii=False)
        else:
            json.dump({'$schema': sch_url, **TOKEN},
                      f, indent=4, ensure_ascii=False)


def switch_config_keys():
    old2new = {'DISCORD_TOKEN': 'discordToken',
               'KAKAO_REST_TOKEN': 'kakaoToken', "COMMAND_PREFIX": 'commandPrefix', 'MESSAGE_COLOR': 'messageColor', 'ALLOW_DM': 'disabledPrivateChannel', 'AUTO_CONNECT': 'connectOnStart'}
    newToken = {'$schema': sch_url}
    for k in TOKEN:
        newkey = old2new.get(k)
        if newkey != None:
            newToken[newkey] = TOKEN[k]
    with open('../data/config.json', 'wt', encoding='utf-8') as f:
        json.dump(newToken,
                  f, indent=4, ensure_ascii=False)
    return newToken


if 'DISCORD_TOKEN' in TOKEN:
    TOKEN = switch_config_keys()
