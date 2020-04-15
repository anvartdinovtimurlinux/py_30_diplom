import time
import requests
import json
import argparse

from progress.bar import IncrementalBar

TOKEN_VK = '709f6974b00c7b3299e7c5e1be0036e73bac6d72a04732e52b240705704df59b00cff81d7dd15c5510ef1'
API_VERSION_VK = 5.103
URL_VK = 'https://api.vk.com/method/'


class User:
    def __init__(self, user_ids):
        if type(user_ids) == int:
            self.user_id = user_ids
        else:
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

    def get_friends(self):
        method = 'friends.get'
        response = get_response(URL_VK, method, self.params)
        return response['response']['items']

    def get_user_groups(self):
        method = 'groups.get'
        self.params['extended'] = 1
        response = get_response(URL_VK, method, self.params)
        return response['response']['items'] if response else []

    def get_user_groups_without_friends(self):
        user_groups = set([group['id'] for group in self.get_user_groups()])
        user_friends = self.get_friends()

        all_friends_groups = set()
        bar = IncrementalBar('Запрос групп, в которых состоят друзья', max=len(user_friends))
        for fr in user_friends:
            friend = User(fr)
            friend_groups = friend.get_user_groups()
            all_friends_groups.update([group['id'] for group in friend_groups])
            bar.next()
        bar.finish()

        method = 'groups.getById'
        user_groups_without_friends = user_groups - all_friends_groups
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
            time.sleep(0.5)
            return get_response(url, method, params)
        elif response['error']['error_code'] == 18 or response['error']['error_code'] == 30:
            # Ошибки 18 и 30 возникают, если пользователь удален или его профиль приватный
            return
        else:
            print(response['error'])
    if response.get('error'):
        pass
    else:
        return response


def arg_parse():
    parser = argparse.ArgumentParser(description='Программа выводит список групп в ВК в которых состоит пользователь,'
                                                 ' но не состоит никто из его друзей')
    parser.add_argument('-n', '--name', type=str, help='Никнейм пользователя или его ID')
    parser.add_argument('-f', '--file', type=str, help='Путь к файлу, в который запишется результат')

    user_name = parser.parse_args().name
    path_to_file = parser.parse_args().file

    if user_name:
        return user_name, path_to_file
    return None, None


def write_json_to_file(data, path_to_file):
    with open(path_to_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Файл {path_to_file} создан')


def main():
    user_id, path_to_file = arg_parse()
    if not user_id:
        user_id = User.get_user_id((input('Введите идентификатор пользователя или его никнейм в VK: ')))
        path_to_file = input('Введите путь к файлу для сохранения результата: ')

    user = User(user_id)
    user_groups_without_friends = user.get_user_groups_without_friends()
    write_json_to_file(user_groups_without_friends, path_to_file)


if __name__ == '__main__':
    main()
