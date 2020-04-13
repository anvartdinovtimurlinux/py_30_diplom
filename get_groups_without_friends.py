import time
from pprint import pprint

import requests
import json
import argparse

TOKEN_VK = '709f6974b00c7b3299e7c5e1be0036e73bac6d72a04732e52b240705704df59b00cff81d7dd15c5510ef1'
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
        print(user_ids)
        params = {
            'user_ids': user_ids,
            'access_token': TOKEN_VK,
            'v': API_VERSION_VK,
        }
        time.sleep(0.5)
        response = requests.get(f'{URL_VK}users.get', params=params)
        return response.json()['response'][0]['id']

    def get_friends(self):
        response = requests.get(f'{URL_VK}friends.get', params=self.params)
        return response.json()['response']['items']

    def get_user_groups(self):
        self.params['extended'] = 1
        try:
            response = requests.get(f'{URL_VK}groups.get', params=self.params)
            return response.json()['response']['items']
        except KeyError:
            return []


# def get_group_members(group_id):
#     params = {
#         'group_id': group_id,
#         'access_token': TOKEN_VK,
#         'v': API_VERSION_VK,
#     }
#     response = requests.get(f'{URL_VK}groups.getMembers', params=params)
#     return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', type=str)
    user_id = parser.parse_args().name
    # if not user_id:
    #     user_id = input('Введите идентификатор пользователя или его ник в VK: ')

    # user = User(user_id)
    user = User('eshmargunov')
    user_groups = set([group['id'] for group in user.get_user_groups()])
    user_friends = user.get_friends()

    pprint(user_friends)
    pprint(user_groups)

    all_friends_groups = set()
    for fr in user_friends:
        friend = User(fr)
        friend_groups = friend.get_user_groups()
        all_friends_groups.update([group['id'] for group in friend_groups])

    print(all_friends_groups)
    print(len(all_friends_groups))

    print(user_groups - all_friends_groups)
    print(len(user_groups - all_friends_groups))


if __name__ == '__main__':
    main()
