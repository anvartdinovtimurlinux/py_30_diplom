import argparse
import json
import itertools
import requests
import sys
import time

from progress.bar import IncrementalBar


class User:
    def __init__(self, user_ids, api, token):
        self.api = api(user_ids, token)
        self.user_id = self.api.get_user_id(user_ids)

    def get_user_friends(self):
        return self.api.get_user_friends()

    def get_user_groups(self):
        return self.api.get_user_groups()

    def get_user_friends_groups(self):
        return self.api.get_user_friends_groups()

    def get_groups_info(self, groups):
        return self.api.get_groups_info(groups)

    def get_user_groups_without_friends(self):
        user_groups = set(self.get_user_groups())
        all_friends_groups = self.get_user_friends_groups()
        user_groups_without_friends = user_groups - all_friends_groups
        groups_info = self.get_groups_info(user_groups_without_friends)

        return [{
            'name': group['name'],
            'gid': group['id'],
            'members_count': group['members_count'],
        } for group in groups_info]


class ApiVK:
    API_VERSION_VK = 5.103
    URL_VK = 'https://api.vk.com/method/'

    def __init__(self, user_ids, token):
        self.TOKEN_VK = token
        self.USER_ID = self.get_user_id(user_ids)

    def get_response(self, method, params):
        response = requests.get(f'{self.URL_VK}{method}', params).json()
        if response.get('error'):
            if response['error']['error_code'] == 6:
                # Слишком много запросов в секунду
                time.sleep(0.5)
                return self.get_response(method, params)
            elif response['error']['error_code'] == 5:
                print('Ошибка авторизации. Убедитесь, что передали верный токен')
                sys.exit()
            else:
                print(response['error'])
                sys.exit()
        else:
            return response['response']

    def get_user_id(self, user_ids):
        if self.__dict__.get('USER_ID'):
            return self.USER_ID
        method = 'users.get'
        params = {
            'user_ids': user_ids,
            'access_token': self.TOKEN_VK,
            'v': self.API_VERSION_VK,
        }
        response = self.get_response(method, params)
        return response[0]['id']

    def get_user_friends(self):
        response = self.get_response('friends.get', {
            'user_id': self.USER_ID,
            'access_token': self.TOKEN_VK,
            'v': self.API_VERSION_VK,
        })
        return response['items']

    def get_user_groups(self):
        response = self.get_response('groups.get', {
            'user_id': self.USER_ID,
            'access_token': self.TOKEN_VK,
            'v': self.API_VERSION_VK,
        })
        return response['items']

    def get_user_friends_groups(self):
        user_friends = self.get_user_friends()
        all_friends_groups = []
        current_user = 0
        requests_in_execute = 25  # число максимальных запросов в методе execute

        bar = IncrementalBar('Запрос групп, в которых состоят друзья', max=len(user_friends))
        while current_user < len(user_friends):
            chunk_friends = user_friends[current_user: current_user + requests_in_execute]
            code = 'var friends_groups = [];' \
                   f'var friends = {chunk_friends};' \
                   'var i = 0;' \
                   'while (i < friends.length) {' \
                   '  friends_groups.push(API.groups.get({"user_id": friends[i], "extended": 0}));' \
                   '  i = i + 1;' \
                   '}' \
                   'return friends_groups;'
            params = {
                'access_token': self.TOKEN_VK,
                'v': self.API_VERSION_VK,
                'code': code,
            }
            method = 'execute'

            response = self.get_response(method, params)
            all_friends_groups.extend([groups['items'] for groups in response if type(groups) == dict])
            current_user += requests_in_execute
            bar.next(25)
        bar.finish()
        return set(itertools.chain.from_iterable(all_friends_groups))

    def get_groups_info(self, groups):
        response = self.get_response('groups.getById', {
            'access_token': self.TOKEN_VK,
            'v': self.API_VERSION_VK,
            'group_ids': ','.join(map(str, groups)),
            'fields': 'members_count',
        })
        return response


def get_params():
    parser = argparse.ArgumentParser(description='Программа выводит список групп в ВК в которых состоит пользователь,'
                                                 ' но не состоит никто из его друзей')
    parser.add_argument('-n', '--name', type=str, help='Никнейм пользователя или его ID')
    parser.add_argument('-f', '--file', type=str, help='Путь к файлу, в который запишется результат')
    parser.add_argument('-t', '--token', type=str, help='Путь к файлу, в котором записан токен VK для запросов')

    user_name = parser.parse_args().name
    path_to_file = parser.parse_args().file
    path_to_token_file = parser.parse_args().token

    if not user_name:
        user_name = input('Введите идентификатор пользователя или его никнейм в VK: ')
    if not path_to_file:
        path_to_file = input('Введите путь к файлу для сохранения результата: ')
    if not path_to_token_file:
        path_to_token_file = input('Введите путь к файлу, в котором записан токен VK для запросов: ')

    return user_name, path_to_file, path_to_token_file


def write_json_to_file(data, path_to_file):
    with open(path_to_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Файл {path_to_file} создан')


def main():
    user_ids, path_to_file, path_to_token_file = get_params()

    with open(path_to_token_file, encoding='utf-8') as f:
        token_vk = f.read().strip()

    user = User(user_ids, ApiVK, token_vk)
    user_groups_without_friends = user.get_user_groups_without_friends()
    write_json_to_file(user_groups_without_friends, path_to_file)


if __name__ == '__main__':
    main()
