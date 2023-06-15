#!/usr/bin/python
#  -*- coding: utf-8 -*-
from typing import Type

import requests
import datetime
from random import randrange, choice
from config import vk_group_token, api_version, access_token
from database import select_users_seen_candidates


def call_server(token: str = vk_group_token, version: str = api_version) -> tuple:
    url: str = 'https://api.vk.com/method/messages.getLongPollServer'
    params: dict = {'access_token': token, 'v': version}
    response: dict = requests.get(url, params=params).json()
    try:
        server: str = response['response']['server']
        key: str = response['response']['key']
        ts: int = response['response']['ts']
        return server, key, ts
    except KeyError:
        return ()

def send_message(user_id: int, message: str, token: str = vk_group_token, version: str = api_version) -> None:
    url: str = 'https://api.vk.com/method/messages.send'
    params: dict = {'access_token': token,
                    'v': version,
                    'random_id': randrange(10 ** 7),
                    'user_id': user_id,
                    'message': message}
    requests.post(url, params=params).json()

def send_photo(user_id: int, candidate_id: int, photo_id: int,
               token: str = vk_group_token, version: str = api_version) -> None:
    url: str = 'https://api.vk.com/method/messages.send'
    params: dict = {'access_token': token,
                    'v': version,
                    'random_id': randrange(10 ** 7),
                    'user_id': user_id,
                    'attachment': f'photo{candidate_id}_{photo_id}'}
    requests.post(url, params=params).json()

def get_person_info(person_id: int, token: str = access_token, version: str = api_version) -> tuple:
    url: str = 'https://api.vk.com/method/users.get'
    params: dict = {'access_token': token,
                    'v': version,
                    'user_ids': person_id}
    response: dict = requests.get(url, params=params).json()
    try:
        first_name: str = response['response'][0]['first_name']
        last_name: str = response['response'][0]['last_name']
        vk_link: str = 'vk.com/id' + str(person_id)
        return first_name, last_name, vk_link
    except KeyError:
        return ()

def ask_sex(user_id: int) -> int:
    server, key, ts = call_server()
    send_message(user_id=user_id, message=f"Укажите, пожалуйста, Ваш пол ('м' или 'ж') без кавычек.")
    while True:
        resp: dict = requests.get(f'https://{server}?act=a_check&key={key}&ts={ts}&wait=90&mode=2&version=2').json()
        try:
            updates: list = resp['updates']
        except KeyError:
            server, key, ts = call_server()
            continue
        if updates:
            for element in updates:
                action_code: int = element[0]
                if action_code == 4:
                    flags = []
                    flag: int = element[2]
                    for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:
                        if flag & number:
                            flags.append(number)
                    if 2 not in flags:
                        text: str = element[5]
                        if text.lower() == 'ж':
                            find_sex: int = 2
                            return find_sex
                        elif text.lower() == 'м':
                            find_sex: int = 1
                            return find_sex
                        else:
                            send_message(user_id=user_id,
                                         message=f"Пол указан неверно. Введите 'м' или 'ж' (без кавычек!).")
        ts: int = resp['ts']

def get_sex(user_id: int, token: str = vk_group_token, version: str = api_version) -> int:
    url: str = 'https://api.vk.com/method/users.get'
    params: dict = {'access_token': token,
                    'v': version,
                    'user_ids': user_id,
                    'fields': 'sex'}
    response: dict = requests.get(url, params=params).json()
    try:
        if 'sex' in response['response'][0]:
            sex: int = response['response'][0]['sex']
            if sex == 1:  # 1 - женский пол
                find_sex: int = 2
            else:  # 2 - мужской пол
                find_sex: int = 1
        else:
            find_sex: int = ask_sex(user_id=user_id)
    except KeyError:
        find_sex: int = ask_sex(user_id=user_id)
    return find_sex

def ask_age(user_id: int) -> int:
    server, key, ts = call_server()
    send_message(user_id=user_id, message=f"Укажите, пожалуйста, Ваш возраст цифрами (от 18 до 65).")
    while True:
        resp: dict = requests.get(f'https://{server}?act=a_check&key={key}&ts={ts}&wait=90&mode=2&version=2').json()
        try:
            updates: list = resp['updates']
        except KeyError:
            server, key, ts = call_server()
            continue
        if updates:
            for element in updates:
                action_code: int = element[0]
                if action_code == 4:
                    flags = []
                    flag: int = element[2]
                    for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:
                        if flag & number:
                            flags.append(number)
                    if 2 not in flags:
                        text: str = element[5]
                        if text.isdigit():
                            if 18 <= int(text) <= 65:
                                age: int = int(text)
                                return age
                            elif int(text) < 18 or int(text) > 65:
                                send_message(user_id=user_id,
                                             message=f"Ваш возраст должен быть не меньше 18 лет и не более 65 лет, "
                                                     f"иначе я не смогу Вам помочь.\n"
                                                     f"Пожалуйста, повторите ввод, если Вы вдруг ошиблись.")
                        else:
                            send_message(user_id=user_id,
                                         message=f"Возраст необходимо указать цифрами. "
                                                 f"Пожалуйста, используйте числа от 18 до 65 включительно.")
        ts: int = resp['ts']

def get_age(user_id: int, token: str = vk_group_token, version: str = api_version) -> int:
    url: str = 'https://api.vk.com/method/users.get'
    params: dict = {'access_token': token,
                    'v': version,
                    'user_ids': user_id,
                    'fields': 'bdate'}
    response: dict = requests.get(url, params=params).json()
    try:
        if 'bdate' in response['response'][0]:
            birthday: str = response['response'][0]['bdate']
            if len(birthday) > 5:  # то есть, если указаны не только дата и месяц, но и год рождения
                birthday_day, birthday_month, birthday_year = map(int, birthday.split('.'))
                today = datetime.date.today()
                age: int = today.year - birthday_year
                if today.month < birthday_month:
                    age -= 1
                elif today.month == birthday_month and today.day < birthday_day:
                    age -= 1
                return age
        else:
            age: int = ask_age(user_id=user_id)
            return age
    except KeyError:
        age: int = ask_age(user_id=user_id)
        return age

def ask_city(user_id: int, token: str = access_token, version: str = api_version) -> int:
    server, key, ts = call_server()
    send_message(user_id=user_id, message=f"Введите, пожалуйста, название Вашего города.\n"
                                          f"Внимание! Сервис работает только по России!")
    while True:
        resp: dict = requests.get(f'https://{server}?act=a_check&key={key}&ts={ts}&wait=90&mode=2&version=2').json()
        try:
            updates: list = resp['updates']
        except KeyError:
            server, key, ts = call_server()
            continue
        if updates:
            for element in updates:
                action_code: int = element[0]
                if action_code == 4:
                    flags = []
                    flag: int = element[2]
                    for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:
                        if flag & number:
                            flags.append(number)
                    if 2 not in flags:
                        city_input: str = element[5]
                        url: str = f'https://api.vk.com/method/database.getCities'
                        params: dict = {'access_token': token,
                                        'v': version,
                                        'country_id': 1,  # ищем только по России
                                        'q': city_input}
                        response: dict = requests.get(url, params=params).json()
                        try:
                            list_cities: list = response['response']['items']
                            if not list_cities:  # []
                                send_message(user_id=user_id,
                                             message=f"К сожалению, я не смог отыскать город с таким именем.\n"
                                                     f"Возможно Вы ошиблись при вводе или ищете город не в России.\n"
                                                     f"Попробуйте снова.")
                            else:
                                for city_info in list_cities:
                                    if city_info['title'].lower() == city_input.lower():
                                        city_id: int = city_info['id']
                                        return city_id
                        except KeyError:
                            return 0
        ts: int = resp['ts']

def get_city(user_id: int, token: str = vk_group_token, version: str = api_version) -> int:
    url: str = 'https://api.vk.com/method/users.get'
    params: dict = {'access_token': token,
                    'v': version,
                    'user_ids': user_id,
                    'fields': 'city'}
    response: dict = requests.get(url, params=params).json()
    try:
        if 'city' in response['response'][0]:
            city_info: dict = response['response'][0]['city']
            city_id: int = city_info['id']  # 1
        else:
            city_id: int = ask_city(user_id=user_id)
    except KeyError:
        city_id: int = ask_city(user_id=user_id)
    return city_id

def search_candidates(user_id: int, token: str = access_token, version: str = api_version) -> int:
    while True:
        url: str = 'https://api.vk.com/method/users.search'
        params: dict = {'access_token': token,
                        'v': version,
                        'count': 1,  # количество возвращаемых кандидатов
                        'offset': randrange(100),
                        'sex': get_sex(user_id),
                        'age_from': get_age(user_id) - 1,
                        'age_to': get_age(user_id) + 1,
                        'city_id': get_city(user_id),
                        'status': choice([1, 5, 6]),  # 1 - не женат / не замужем, 5 — всё сложно, 6 — в активном поиске
                        'has_photo': 1}  # только с фотографией профиля!
        response: dict = requests.get(url, params=params).json()
        try:
            info = response['response']['items']
            if info[0]:
                candidate = info[0]  # словарь с информацией о кандидате
                if not candidate['is_closed'] or candidate['is_closed'] and candidate['can_access_closed']:
                    if not select_users_seen_candidates(user_id=user_id, candidate_id=candidate['id']):
                        return candidate['id']
        except KeyError:
            return 0

def get_candidate_photo_id(candidate_id: int, token: str = access_token, version: str = api_version) -> list:
    url: str = 'https://api.vk.com/method/photos.get'
    params: dict = {'access_token': token,
                    'v': version,
                    'owner_id': candidate_id,
                    'album_id': 'profile',
                    'extended': 1}  # будут возвращены дополнительные поля: likes, comments, tags, can_comment, reposts
    response: dict = requests.get(url, params=params).json()
    try:
        all_photos: list = response['response']['items']  # список словарей (каждый словарь - информация об одной фотке)
        all_photos_id: list = [item['id'] for item in all_photos]  # список из id всех фоток кандидата
        if 1 <= len(all_photos_id) <= 3:
            best_photos_id: list = all_photos_id  # отсылаем юзеру все фотки, что есть у потенциального кандидата
        else:  # т.к. мы изначально запрашиваем кандидатов только с фотографиями профиля, то значит их больше трёх !!!
            best_photo_dict = {}
            likes_comments_summand = []
            for item in all_photos:
                best_photo_dict.update({item['id']: item['comments']['count'] + item['likes']['count']})
                likes_comments_summand.append(item['comments']['count'] + item['likes']['count'])
            sorted_summand = sorted(likes_comments_summand, reverse=True)
            best_photos_id = []
            for summa in sorted_summand[:3]:
                for key, value in best_photo_dict.items():
                    if summa == value:
                        if len(best_photos_id) < 3:  # если несколько фоток имеют одно и то же количество лайков
                            best_photos_id.append(key)
                        else:
                            break
        return best_photos_id
    except KeyError:
        return []
