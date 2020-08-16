import requests
import os
import sys

base_url = 'https://gitlab.com/api/v4'
req_headers = {'PRIVATE-TOKEN': os.getenv('TOOL_API_KEY')}
project_id = os.getenv('CI_PROJECT_ID')


def requests_API(method, link, datadict=None):
    method = method.upper()
    if method == "POST":
        x = requests.post(base_url + link,
                          data=datadict, headers=req_headers)
    elif method == "PUT":
        x = requests.put(base_url + link,
                         data=datadict, headers=req_headers)
    elif method == 'GET':
        x = requests.get(base_url + link, headers=req_headers)
    return x


def pre_release():
    mr_data = requests_API(
        'GET', '/projects/{}/merge_requests?state=merged&not[labels][]=workflow::verification&not[labels][]=workflow::production&target_branch=master'.format(project_id)).json()
    for d in mr_data:
        requests_API(
            'PUT', '/projects/{}/merge_requests/{}'.format(project_id, d['iid']), {'add_labels': 'workflow::verification'})


def stable_release():
    tag_name = os.getenv('CI_COMMIT_TAG')

    mr_data = requests_API(
        'GET', '/projects/{}/merge_requests?state=merged&labels=workflow::verification&target_branch=master&sort=asc'.format(project_id)).json()

    data_dict = {}
    for d in mr_data:
        data_dict[d['iid']] = d['squash_commit_sha']

    for k, v in data_dict.items():
        ls = requests_API(
            'GET', '/projects/{}/repository/commits/{}/refs'.format(project_id, v)).json()
        for x in ls:
            if (x['type'] == 'tag') and (x['name'] == tag_name):
                requests_API(
                    'PUT', '/projects/{}/merge_requests/{}'.format(project_id, k), {'add_labels': 'workflow::production'})
                break

    requests_API(
        'PUT', '/projects/{}/badges/{}'.format(project_id, 79762), {'image_url': 'https://img.shields.io/badge/Stable Release-{}-skyblue?logo=Azure+Pipelines&logoColor=white'.format(tag_name)})


try:
    if '-b' in sys.argv:
        pre_release()
    elif '-r' in sys.argv:
        stable_release()
except Exception as e:
    import traceback
    traceback.print_exc()
    pass
