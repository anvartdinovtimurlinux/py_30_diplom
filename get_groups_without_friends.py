import argparse
import json
import itertools
import requests
import sys
import time

from progress.bar import IncrementalBar


API_VERSION_VK = 5.103
URL_VK = 'https://api.vk.com/method/'


class User:
    def __init__(self, user_ids):
        self.user_id = User.get_user_id(user_ids)

        self.params = {
            'user_id': self.user_id,
            'access_token': TOKEN_VK,
            'v': API_VERSION_VK,
        }

    @staticmethod
    def get_user_id(user_ids):
        method = 'users.get'
        params = {
            'user_ids': user_ids,
            'access_token': TOKEN_VK,
            'v': API_VERSION_VK,
        }
        response = get_response(URL_VK, method, params)
        return response['response'][0]['id']

    def get_user_friends(self):
        method = 'friends.get'
        response = get_response(URL_VK, method, self.params)
        return response['response']['items']

    def get_user_groups(self):
        method = 'groups.get'
        # self.params['extended'] = 1
        response = get_response(URL_VK, method, self.params)
        return response['response']['items'] if response else []

    def get_user_friends_groups(self):
        user_friends = self.get_user_friends()
        all_friends_groups = []
        current_user = 0

        bar = IncrementalBar('Запрос групп, в которых состоят друзья', max=len(user_friends))
        while current_user < len(user_friends):
            chunk_friends = user_friends[current_user: current_user + 25]
            code = 'var friends_groups = [];' \
                   'var friend_groups;' \
                   f'var friends = {chunk_friends};' \
                   'var i = 0;' \
                   'while (i < friends.length) {' \
                   '  friend_groups = API.groups.get({"user_id": friends[i], "extended": 0});' \
                   '  friends_groups.push(friend_groups);' \
                   '  i = i + 1;' \
                   '}' \
                   'return friends_groups;'
            params = {
                # 'user_id': 171691064,
                'access_token': TOKEN_VK,
                'v': API_VERSION_VK,
                'code': code,
            }
            method = 'execute'

            response = get_response(URL_VK, method, params)
            all_friends_groups.extend([groups['items'] for groups in response['response'] if type(groups) == dict])
            current_user += 25  # число максимальных запросов в методе execute
            bar.next(25)
        bar.finish()
        return set(itertools.chain.from_iterable(all_friends_groups))

    def get_user_groups_without_friends(self):
        user_groups = set(self.get_user_groups())
        all_friends_groups = self.get_user_friends_groups()
        user_groups_without_friends = user_groups - all_friends_groups

        method = 'groups.getById'
        self.params['group_ids'] = ','.join(map(str, user_groups_without_friends))
        self.params['fields'] = 'members_count'
        response = get_response(URL_VK, method, self.params)

        return [{
            'name': group['name'],
            'gid': group['id'],
            'members_count': group['members_count'],
        } for group in response['response']]


def get_response(url, method, params):
    response = requests.get(f'{url}{method}', params=params).json()
    if response.get('error'):
        if response['error']['error_code'] == 6:
            # Слишком много запросов в секунду
            time.sleep(0.5)
            return get_response(url, method, params)
        elif response['error']['error_code'] == 5:
            print('Ошибка авторизации. Убедитесь, что передали верный токен')
            sys.exit()
        elif response['error']['error_code'] == 18 or response['error']['error_code'] == 30:
            # Ошибки 18 и 30 возникают, если пользователь удален или его профиль приватный
            return
        else:
            print(response['error'])
            sys.exit()
    else:
        return response


def arg_parse():
    parser = argparse.ArgumentParser(description='Программа выводит список групп в ВК в которых состоит пользователь,'
                                                 ' но не состоит никто из его друзей')
    parser.add_argument('-n', '--name', type=str, help='Никнейм пользователя или его ID')
    parser.add_argument('-f', '--file', type=str, help='Путь к файлу, в который запишется результат')
    parser.add_argument('-t', '--token', type=str, help='Путь к файлу, в котором записан токен VK для запросов')

    user_name = parser.parse_args().name
    path_to_file = parser.parse_args().file
    path_to_token_file = parser.parse_args().token

    if user_name:
        return user_name, path_to_file, path_to_token_file
    return None, None, None


def write_json_to_file(data, path_to_file):
    with open(path_to_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Файл {path_to_file} создан')


def main():
    user_id, path_to_file, path_to_token_file = arg_parse()
    if not user_id:
        user_id = User.get_user_id((input('Введите идентификатор пользователя или его никнейм в VK: ')))
    if not path_to_file:
        path_to_file = input('Введите путь к файлу для сохранения результата: ')
    if not path_to_token_file:
        path_to_token_file = input('Введите путь к файлу, в котором записан токен VK для запросов: ')

    with open(path_to_token_file, encoding='utf-8') as f:
        global TOKEN_VK
        TOKEN_VK = f.read().strip()

    user = User(user_id)
    user_groups_without_friends = user.get_user_groups_without_friends()
    write_json_to_file(user_groups_without_friends, path_to_file)


if __name__ == '__main__':
    main()
