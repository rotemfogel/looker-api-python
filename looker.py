import json
import os
from pprint import pprint

import requests
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
_endpoint = os.getenv('ENDPOINT')


def _read(file: str) -> dict:
    fl = file if file.endswith('.json') else f'{file}.json'
    f = open(fl, 'r')
    lines = f.readlines()
    f.close()
    return json.loads(''.join(lines))


def _write(what, fn):
    f = open("{}.json".format(what), "w")
    f.write(json.dumps(fn, indent=2))
    f.close()


class LookerApi:
    def __init__(self):
        self._client_id = os.getenv('CLIENT_ID')
        self._client_secret = os.getenv('CLIENT_SECRET')
        self._URL = 'https://{}:19999/api/3.1/'.format(_endpoint)
        self._headers = {
            'Authorization': 'token {}'.format(self._generate_auth_token())
        }

    def _generate_auth_token(self):
        """
        Generates an access token for the Looker API that can be passed in the required authorization header.
        These tokens expire in an hour
        """
        print('acquiring token...')
        data = {
            'client_id': self._client_id,
            'client_secret': self._client_secret
        }
        auth_token = requests.post(self._URL + 'login', data=data)
        print('token acquired.')
        return auth_token.json().get('access_token')

    def get_all_dashboards(self):
        def get_dashboard(dash_id: int) -> str:
            return self.get(f'dashboards/{dash_id}')

        dashboards = self.get('dashboards')
        dashboard_ids = list(map(lambda x: x['id'], dashboards))
        dashboards = []
        for dashboard_id in dashboard_ids:
            dashboards.append(get_dashboard(dashboard_id))
        return dashboards

    def get_all_users(self):
        return self.get('users')

    def get_all_groups(self):
        return self.get('groups')

    def get_all_roles(self):
        return self.get('roles')

    def get(self, what):
        response = requests.get(self._URL + what, headers=self._headers)
        print('retrieved {}'.format(what))
        return response.json()


def _process_logins():
    users = _read('users.json')
    active = list(filter(lambda u: not u['is_disabled'] and str(u['email']).endswith('seekingalpha.com'), users))
    print('total {}\nactive {}'.format(len(users), len(active)))
    users = list(
        map(lambda x: {'id': x['id'], 'email': x['email'], 'groups': x['group_ids'], 'roles': x['role_ids']}, active))
    roles = list(map(lambda x: {x['id']: x['name'], 'permissions': x['permission_set']['permissions']}, _read('roles')))
    groups = list(map(lambda x: {x['id']: x['name']}, _read('groups')))
    groupps = []
    for group in groups:
        for k, v in group.items():
            groupps.append("({}, '{}')".format(k, v))
    print('insert into looker_groups values ' + ','.join(groupps))

    # permissions = list(map(lambda x: x['permissions'], roles))
    permissions = [{'access_data': 1}, {'administer': 2}, {'create_alerts': 3}, {'create_prefetches': 4},
                   {'create_public_looks': 5}, {'create_table_calculations': 6}, {'deploy': 7}, {'develop': 8},
                   {'download_with_limit': 9}, {'download_without_limit': 10}, {'embed_browse_spaces': 11},
                   {'explore': 12}, {'follow_alerts': 13}, {'login_special_email': 14}, {'manage_homepage': 15},
                   {'manage_models': 16}, {'manage_spaces': 17}, {'save_content': 18}, {'save_sql_runner_content': 19},
                   {'schedule_external_look_emails': 20}, {'schedule_look_emails': 21}, {'see_datagroups': 22},
                   {'see_drill_overlay': 23}, {'see_logs': 24}, {'see_lookml': 25}, {'see_lookml_dashboards': 26},
                   {'see_looks': 27}, {'see_pdts': 28}, {'see_queries': 29}, {'see_schedules': 30}, {'see_sql': 31},
                   {'see_sql_runner_content': 32}, {'see_system_activity': 33}, {'see_user_dashboards': 34},
                   {'see_users': 35}, {'send_outgoing_webhook': 36}, {'send_to_integration': 37}, {'send_to_s3': 38},
                   {'send_to_sftp': 39}, {'sudo': 40}, {'support_access_toggle': 41}, {'update_datagroups': 42},
                   {'use_sql_runner': 43}]
    role_permissions = []
    for role in roles:
        perms = role['permissions']
        ints = []
        for perm in perms:
            for p in permissions:
                for k, v in p.items():
                    if perm == k:
                        ints.append(str(v))
                        break
        keys = list(role.keys())
        role_permissions.append({'id': keys[0], 'permissions': ints})
    role_perms = []
    for role_perm in role_permissions:
        perms = role_perm['permissions']
        for perm in perms:
            role_perms.append('({}, {})'.format(role_perm['id'], perm))
    print('insert into looker_role_permissions values ' + ','.join(role_perms) + ';')

    user_groups = []
    user_roles = []
    user_emails = []
    for user in users:
        for group in user['groups']:
            user_groups.append('({}, {})'.format(user['id'], group))
        for role in user['roles']:
            user_roles.append('({}, {})'.format(user['id'], role))
        user_emails.append("({}, '{}')".format(user['id'], user['email']))

    print('insert into looker_user_groups values ' + ','.join(user_groups) + ';')
    print('insert into looker_user_roles values ' + ','.join(user_roles) + ';')
    print('insert into looker_users values ' + ','.join(user_emails) + ';')
    # print(groups)
    # print(users)


def _dashboards_with_more_than_25_elements():
    url_prefix = f'https://{_endpoint}/dashboards/'
    dashboards = _read('dashboards.json')
    dash = list(filter(lambda x: 'thelook::' not in str(x['link']),
                       map(lambda x: {'id': x['id'],
                                      'link': url_prefix + str(x['id']),
                                      'title': x['title'],
                                      'folder': x['space']['name'],
                                      'layouts': x['dashboard_layouts'][0]['dashboard_layout_components']
                                      }, dashboards)))
    more_than_25 = list(map(lambda x: {'title': x['title'], 'link': x['link'], 'elements': len(x['layouts'])},
                            filter(lambda x: len(x['layouts']) > 25, dash)))
    pprint(more_than_25)


def main():
    # looker_api = LookerApi()
    # _write('dashboards', looker_api.get_all_dashboards())
    # _write('users', looker_api.get_all_users())
    # _write('roles', looker_api.get_all_roles())
    # _write('groups', looker_api.get_all_groups())
    # _write('swagger', looker_api.get('swagger.json'))
    # _write('looks', looker_api.get('looks'))
    _process_logins()
    # _dashboards_with_more_than_25_elements()
    # dashboards = _read('dashboards')
    # titles = list(
    #     map(lambda x: {'dashboard': x['title'], 'tiles': list(
    #         filter(lambda z: z is not None, list(map(lambda y: y['title'], x['dashboard_elements']))))},
    #         dashboards))
    # print(json.dumps(titles, indent=1))
    # # dash_list = [11, 38, 84, 97, 112, 133, 147, 148, 155, 158, 170, 182, 189, 224, 225, 227, 236, 241, 252,
    # #              298, 304, 308, 311, 317, 346, 347]
    # dash_list = [158, 83, 310]
    # dash_list = [369]
    # layouts = list(filter(lambda x: x['id'] in dash_list, dash))[-1]['layouts']
    # titles = list(map(lambda x: str(x['element_title']).replace('Premium', 'Marketplace'), layouts))
    # print(json.dumps(titles, indent=1))
    #     for layout in d['layouts']:
    #         if layout['element_title'] and not layout['deleted']:
    #             print(f',,"{layout["element_title"]}"')
    # less_than_5 = list(filter(lambda x: len(x['layouts']) < 5, dash))
    # print(less_than_5)
    # print(sorted(less_than_5, key=lambda x: x['id']))
    # users = _read('users.json')
    # active = list(filter(lambda u: not u['is_disabled'] and str(u['email']).endswith('seekingalpha.com'), users))
    # print('\n'.join(sorted(list(map(lambda x: f"{x['id']},{x['email']},{str(x['is_disabled']).lower()}", users)))))


if __name__ == "__main__":
    main()
