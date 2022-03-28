import time
from db import db
import vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


mylogin = "login"
mypassword = "password"
token_group = "token group"


class VkGroup:

    def __init__(self, login, password, token):
        self.login = login
        self.password = password
        self.token_group = token
        self.receive_message = vk.Communication(self.token_group).listen()
        self.mess_id = self.receive_message[0]
        self.sending_message = vk.Communication(self.token_group)
        self.admin_group = vk.User(self.login, self.password)

    def mess_text(self):
        receive_message = vk.Communication(self.token_group).listen()
        return receive_message[1]

    # подготовка данных для поиска
    def data_checking(self):
        user_vk = self. admin_group.users_id(self.mess_id)
        search_term = self.admin_group.requirements(user_vk)

        # запрашиваем не достающую информацию
        # возраст
        if search_term["age_from"] is None and search_term["age_to"] is None:
            self.sending_message.send_message(self.mess_id, f"Не хватает данных для поиска")
            self.sending_message.send_message(self.mess_id, f"Введите свой возраст")
            receive_message = vk.Communication(token_group).listen()
            search_term["age_from"] = int(receive_message[1]) - 2
            search_term["age_to"] = int(receive_message[1]) + 2

        # пол
        if search_term["sex"] is None:
            self.sending_message.send_message(self.mess_id, f"Укажите пол для поиска")
            self.sending_message.send_message(self.mess_id, f"Выбирите одну из цифр")
            self.sending_message.send_message(self.mess_id, f"1 - женский 2 - мужской")
            receive_message = vk.Communication(token_group).listen()
            search_term["sex"] = int(receive_message[1])

        # город
        if search_term["age_to"] is None:
            self.sending_message.send_message(self.mess_id, f"Укажите город для поиска")
            self.sending_message.send_message(self.mess_id, f"Введите название города")
            receive_message = vk.Communication(token_group).listen()
            search_term["city"] = receive_message[1]
        return search_term

    # Отбор кандидатов и выбор 3 фото
    def selection_candidates(self, arg, arg_1):
        self.sending_message.send_message(self.mess_id, f"идет поиск кандидатов")
        user_search = self.admin_group.user_search(arg, arg_1)
        user_top_photo = self.admin_group.top_photo(user_search)
        return user_top_photo

    # подготовка к показу и вывод кандидатов в чат
    def show_photo(self, arg):
        for i in arg:
            uid, url = i.items()
            photo_url = list(url[1][0].items())
            show_can = self.admin_group.users_id(uid[0])
            first_name = show_can[0].get("first_name")
            last_name = show_can[0].get("last_name")
            self.sending_message.send_message(self.mess_id, f"{first_name} {last_name}")
            self.sending_message.send_message_media(self.mess_id, f"photo{uid[0]}_{photo_url[0][0]}")
            time.sleep(1)
        self.sending_message.send_message(self.mess_id, f"поиск окончен")


def main():
    con = db.create_database("db_vk")
    vk_bot = VkGroup(mylogin, mypassword, token_group)
    # Создание кнопки
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('поиск кандидатов', color=VkKeyboardColor.SECONDARY)

    while True:
        elimination_id = db.select_user_id(con)
        vk_bot.sending_message.send_message(vk_bot.mess_id,
                                            "нажмите на поиск кандидатов ", keyboard=keyboard.get_keyboard())
        if vk_bot.mess_text() == "поиск кандидатов":
            search_term = vk_bot.data_checking()
            user_top_photo = vk_bot.selection_candidates(search_term, elimination_id)
            # Запись в базу данных
            db.insert_data(con, user_top_photo)
            # Показ кандидатов
            vk_bot.show_photo(user_top_photo)
        else:
            vk_bot.sending_message.send_message(vk_bot.mess_id, f"Я умею только искать, так что нажми кнопку поиск")


if __name__ == '__main__':
    main()
