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
