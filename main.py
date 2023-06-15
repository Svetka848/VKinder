#!/usr/bin/python
#  -*- coding: utf-8 -*-
from database import create_tables, select_users, insert_users, insert_users_seen_candidates
from vk import *


def main() -> None:

    try:
        server, key, ts = call_server()

    except Exception:
        return print("Проблемы с токеном. Проверьте актуальность токена сообщества.")

    create_tables()

    while True:
        resp: dict = requests.get(f'https://{server}?act=a_check&key={key}&ts={ts}&wait=90&mode=2&version=2').json()

        try:
            updates: list = resp['updates']

        except KeyError:  # если здесь возбуждается исключение KeyError, то параметр key устарел, и нужно получить новый
            server, key, ts = call_server()
            continue

        if updates:  # проверка, были ли обновления
            for element in updates:
                action_code: int = element[0]

                if action_code == 4:  # цифра 4 - это новое сообщение

                    # научим программу отличать исходящие сообщения от входящих:
                    flags = []
                    flag = element[2]
                    for number in [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 65536]:
                        if flag & number:
                            flags.append(number)
                    if 2 not in flags:  # если это не исходящее сообщение, то:

                        # NB! Если юзер не в сети, то его id начинается с минуса - берём модуль на всякий случай!
                        user_id = abs(element[3])  # получаем id написавшего юзера
                        text = element[5]  # получаем текст сообщения юзера

                        try:

                            if text.lower() == 'начать':

                                send_message(user_id=user_id,
                                             message=f"Рад Вас приветствовать, {get_person_info(person_id=user_id)[0]}!"
                                                     f"\n\nЯ чат-бот VKinder и сейчас я постараюсь подобрать Вам пару."
                                                     f"\n\nК сожалению, я только учусь, поэтому мне очень важно, "
                                                     f"чтобы Вы правильно отвечали на мои вопросы."
                                                     f"\n\nВведите 'да', если Вы готовы насладиться первым кандидатом.")

                            elif text.lower() == 'да':

                                vk_id = search_candidates(user_id=user_id)

                                vk_name, vk_surname, vk_link = get_person_info(person_id=vk_id)

                                send_message(user_id=user_id, message=f"{vk_name} {vk_surname}\n{vk_link}")

                                for index, value in enumerate(get_candidate_photo_id(vk_id)):
                                    send_photo(user_id=user_id, candidate_id=vk_id,
                                               photo_id=get_candidate_photo_id(vk_id)[index])

                                if not select_users(user_id):
                                    insert_users(user_id=user_id)

                                insert_users_seen_candidates(user_id=user_id, candidate_id=vk_id)

                                send_message(user_id=user_id,
                                             message=f"Желаете продолжить? Тогда смело вводите 'да'.\n\n"
                                                     f"Если Вы уже подобрали себе пару - введите 'нет'.")

                            elif text.lower() == 'нет':
                                send_message(user_id=user_id, message=f"Рад был Вам помочь! Надеюсь, я был полезен! :)"
                                                                      f"\n\nЗахотите повторить - введите 'начать'!")

                            else:
                                # Работа с БД, чтобы бот не реагировал на сообщения, запрашивающие у юзера доп. инфу
                                if not select_users(user_id=user_id):  # отправляем подсказку новому юзеру только 1 раз!
                                    send_message(user_id=user_id,
                                                 message=f"Введите \'начать\', чтобы я смог начать поиск партнера.")

                        except Exception:
                            send_message(user_id=user_id,
                                         message=f"Ошибка доступа. Похоже, что возникли проблемы с токеном.")

        ts: int = resp['ts']  # обновление номера ts последнего обновления


if __name__ == '__main__':
    main()
