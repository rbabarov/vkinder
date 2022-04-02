from datetime import datetime
import random
import json
import time
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

#  Запись результата в файл
def write_json(data_to_write):
    with open('top_10_users.json', 'w', encoding='utf-8') as file:
        json.dump(data_to_write, file, ensure_ascii=False, indent=2)

class User:

    def __init__(self, login=None, password=None, token=None):

        if token != None:
        # self.vk_session = vk_api.VkApi(login, password)
             self.vk_session = vk_api.VkApi(token=token)
        else:
            self.vk_session = vk_api.VkApi(login, password)

        self.vk_session.auth()
        self.vk = self.vk_session.get_api()

    # Получаем информацию о полтзователе
    def users_id(self, uid=None):
        user_information = self.vk.users.get(user_ids=uid, fields="bdate, sex, city, relation")
        time.sleep(0.27)
        return user_information

    # Составляем условия поиска
    @staticmethod
    def requirements(arg):
        requirements = {}
        # возраст
        age = arg[0].get('bdate')
        if age is not None and len(age.split(".")) == 3:
            year_birth = datetime.strptime(age, '%d.%m.%Y').year
            this_year = datetime.now().year
            requirements["age_from"] = this_year - year_birth - 2
            requirements["age_to"] = this_year - year_birth + 2
        else:
            requirements["age_from"] = None
            requirements["age_to"] = None
        # пол
        sex = arg[0].get('sex')
        if sex == 1:
            sex = 2
        elif sex == 2:
            sex = 1
        else:
            sex = None
        requirements["sex"] = sex
        # город
        city = arg[0].get('city').get('title')
        if city is not None:
            requirements["city"] = city
        else:
            requirements["city"] = None
        return requirements

    # Ищем 10 пользователей с подходящими условиями
    def user_search(self, arg, elimination_id):
        sex = arg["sex"]
        hometown = arg["city"]
        status = 1
        age_from = arg["age_from"]
        age_to = arg["age_to"]
        user_search = self.vk.users.search(count=1000, hometown=hometown,
                                           sex=sex, status=status,
                                           age_from=age_from, age_to=age_to,
                                           fields="is_closed")
        time.sleep(0.27)
        address_list = []
        for i in user_search["items"]:
            address_dict = {}
            if i["can_access_closed"] and len(address_list) < 10:
                if i["id"] not in elimination_id:
                    address_dict[i["id"]] = "https://vk.com/id" + str(i["id"])
                    address_list.append(address_dict)
        return address_list

    # Добавляем топ 3 фото пользователя в список кандидатов
    def top_photo(self, list_candidates):
        for i in list_candidates:
            # Получаем список фото пользователя
            uid = i.keys()
            top3photo = self.vk.photos.get(owner_id=uid, album_id="profile", extended=1)
            time.sleep(0.27)
            # Создаем список лайков и сортируем по убыванию
            likes_list = []
            for likes_i in top3photo["items"]:
                likes_list.append(likes_i["likes"]["count"])
            likes_list.sort(reverse=True)
            # Получаем три ссылки на фото с наибольшим кол-вом лайков
            list_url_photo = []
            for photo_i in top3photo["items"]:
                if photo_i["likes"]["count"] in likes_list[0: 3]:
                    list_url_photo.append({photo_i["id"]: photo_i["sizes"][-1]["url"]})
            # Добовляем список uri фото в список пользователей
            i["url_photo"] = list_url_photo
        # JSON-файл с 10 объектами, где у каждого объекта перечислены топ-3 фотографии и ссылка на аккаунт.
        write_json(list_candidates)

        return list_candidates


# Communicate group class
class Communication:

    def __init__(self, token):
        self.token = token
        self.vk = vk_api.VkApi(token=self.token)
        self.vk._auth_token()
        self.longpol = VkLongPoll(self.vk)

    # listen server
    def listen(self):
        for event in self.longpol.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    return int(event.user_id), event.text
                break

    # send message
    def send_message(self, user_id, text, keyboard=None, template=None):
        self.vk.method("messages.send", {"user_id": user_id, "message": text,
                                         "random_id": random.randrange(10 ** 7),
                                         "keyboard": keyboard, "template": template})

    # send file
    def send_message_media(self, user_id, arg):
        self.vk.method("messages.send", {"user_id": user_id,
                                         "random_id": random.randrange(10 ** 7),
                                         "attachment": arg})
