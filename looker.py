import json
import os
from pprint import pprint
from typing import Optional

import pendulum
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
        print('-- acquiring token...')
        data = {
            'client_id': self._client_id,
            'client_secret': self._client_secret
        }
        auth_token = requests.post(self._URL + 'login', data=data)
        print('-- token acquired.')
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
        print('-- retrieved {}'.format(what))
        return response.json()


_logged_in_at: str = 'logged_in_at'


def _get_last_login(r: dict) -> Optional[str]:
    def get_last_login(what: str) -> str:
        _result = None
        if r.get(what):
            _result = r[what].get(_logged_in_at)
        return _result

    credentials: str = 'credentials_'
    for t in ['google', 'email', 'embed', 'ldap',
              'looker_openid', 'oidc', 'saml', 'totp']:
        result = get_last_login(f'{credentials}{t}')
        if result:
            break
    return pendulum.parse(result).format('YYYY-MM-DD') if result else None


def _process_logins():
    for table in ['user_groups', 'user_roles', 'roles', 'groups', 'users']:
        print(f'delete from looker_{table};')
    users = _read('users.json')
    # active = list(filter(lambda u: not u['is_disabled'] and str(u['email']).endswith('seekingalpha.com'), users))
    # print('total {}\nactive {}'.format(len(users), len(active)))

    userss = list(
        map(lambda x: {'id': x['id'], 'email': x['email'], 'enabled': not x['is_disabled'],
                       _logged_in_at: _get_last_login(x), 'groups': x['group_ids'],
                       'roles': x['role_ids']}, users))
    roles = list(map(lambda x: {x['id']: x['name']}, _read('roles')))
    roless = []
    for role in roles:
        for k, v in role.items():
            roless.append("({}, '{}')".format(k, v))
    print('insert into looker_roles values ' + ','.join(roless) + ';')

    groups = list(map(lambda x: {x['id']: x['name']}, _read('groups')))
    groupps = []
    for group in groups:
        for k, v in group.items():
            groupps.append("({}, '{}')".format(k, v))
    print('insert into looker_groups values ' + ','.join(groupps) + ';')

    user_groups = []
    user_roles = []
    user_emails = []
    for user in userss:
        for group in user['groups']:
            user_groups.append('({}, {})'.format(user['id'], group))
        for role in user['roles']:
            user_roles.append('({}, {})'.format(user['id'], role))
        user_emails.append("({}, '{}', {}, {})".format(user['id'], user['email'],
                                                       str(user['enabled']).lower(),
                                                       f"'{user[_logged_in_at]}'" if user.get(
                                                           _logged_in_at) else 'null'))

    print('insert into looker_users values ' + ','.join(user_emails) + ';')
    print('insert into looker_user_groups values ' + ','.join(user_groups) + ';')
    print('insert into looker_user_roles values ' + ','.join(user_roles) + ';')
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
    looker_api = LookerApi()
    # _write('dashboards', looker_api.get_all_dashboards())
    _write('users', looker_api.get_all_users())
    _write('roles', looker_api.get_all_roles())
    _write('groups', looker_api.get_all_groups())
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
