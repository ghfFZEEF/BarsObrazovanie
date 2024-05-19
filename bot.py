from telebot import TeleBot, types
from sqlite3 import connect
from requests import Session
from datetime import date, timedelta, datetime
from fake_useragent import UserAgent
from re import sub
from csv import writer
from os import remove
from typing import Union


class TgBot(TeleBot):
    def __init__(self, token: str) -> None:
        super().__init__(token)

    def __start(self, message: types.Message) -> None:
        user_name: str = message.from_user.first_name
        self.send_message(message.chat.id, f'Доброго времени суток, <b>{user_name}</b>', parse_mode='html')
        db = connect('data/users.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM data WHERE user_id = ? ", (message.chat.id,))
        data = cursor.fetchall()
        cursor.close()
        db.close()
        if len(data) != 0:
            if self.__check_reg(message.chat.id):
                self.send_message(message.chat.id, 'Вы уже авторизованны и можете пользоваться всеми функциями',
                                  reply_markup=self.__markup_all())
            else:
                self.__error(message.chat.id)
        else:
            self.send_message(message.chat.id, 'Чтобы пользоваться функциями бота, пройдите регистрацию',
                              reply_markup=self.__markup_reg())

    def __help(self, message: types.Message) -> None:
        if self.__check_reg(message.chat.id):
            self.send_message(message.chat.id, 'Если вам понадобится помощь, воспользуйтесь командой "Помощь"',
                              reply_markup=self.__markup_all())
            self.send_message(message.chat.id, 'Так же вы можете похвалить бота, написав (Бот, ты молодец)')

        else:
            self.send_message(message.chat.id, 'Если вам понадобится помощь, воспользуйтесь командой "Помощь"')
            self.send_message(message.chat.id, 'Что бы пользоваться функциями бота, пройдите регистрацию)',
                              reply_markup=self.__markup_reg())

    def __all_messages(self, message: types.Message) -> None:
        if message.text == 'Начать регистрацию':
            self.send_message(message.chat.id, 'Введите ваш пароль от БАРС', reply_markup=types.ReplyKeyboardRemove())
            self.register_next_step_handler(message, self.__reg_pas)

        elif message.text == 'Оценки':
            self.send_message(message.chat.id, 'Сею секунду, господин')
            self.__grades(message.chat.id)

        elif message.text == 'Домашнее задание':
            self.send_message(message.chat.id, 'Выберете, на когда вы хотите узнать домашнее задание',
                              reply_markup=self.__markup_day())
        elif message.text == 'Д/З на сегодня':
            self.__hw(message, date.today())
        elif message.text == 'Д/З на завтра':
            self.__hw(message, str(datetime.today() + timedelta(days=1))[:10])
        elif message.text == 'Выбрать свою дату':
            self.send_message(message.chat.id, 'Введите дату вида «гггг-мм-дд»')
            self.register_next_step_handler(message, self.__hw)

        elif message.text == 'Педагогический состав':
            self.send_message(message.chat.id, 'Сею секунду, господин')
            self.__teachers(message.chat.id)

        elif message.text == 'Помощь':
            self.send_message(message.chat.id, 'В любое время можете обратиться к нашему менеджеру t.me//I_or_not_I')

        elif message.text == 'Изменить аккаунт':
            self.__delete_account(message)
            self.send_message(message.chat.id, 'Вы решили изменить свои данные, '
                                               'поэтому вам придется заново пройти регистрацию',
                              reply_markup=self.__markup_reg())

        elif message.text == 'Моя учетная запись':
            db = connect('data/users.db')
            cursor = db.cursor()
            cursor.execute("SELECT pass FROM data WHERE user_id = ? ", (message.chat.id,))
            pas = cursor.fetchone()[0]
            cursor.execute("SELECT login FROM data WHERE user_id = ? ", (message.chat.id,))
            log = cursor.fetchone()[0]
            cursor.close()
            db.close()

            self.send_message(message.chat.id, f'Ваш логин: {log}')
            self.send_message(message.chat.id, f'Ваш пароль: {pas}')

        elif message.text == 'Бот, ты молодец':
            self.send_message(message.chat.id, 'Спасибо огромное, можете поддержать моего автора, '
                                               'скинув деньги по номеру карты: 2200_7005_9155_1949 - '
                                               'Тинькофф или 2202_2023_9149_4329 - Сбер (Руслан Олегович К.)')

        else:
            self.send_message(message.chat.id, 'Я не знаю такой команды(')

    def __photo(self, message: types.Message) -> None:
        self.reply_to(message, 'Отличное фото')

    def run(self) -> None:
        self.register_message_handler(self.__start, commands=["start"])
        self.register_message_handler(self.__help, commands=["help"])
        self.register_message_handler(self.__delete_account, commands=["del_acc"])
        self.register_message_handler(self.__admin, commands=["admin"])

        self.register_message_handler(self.__all_messages, content_types=['text'])
        self.register_message_handler(self.__photo, content_types=['photo'])

        # self.polling(none_stop=True, interval=0)
        self.infinity_polling()

    def __error(self, chat_id: int) -> None:
        self.send_message(chat_id, 'Вы ввели некорректные данные, их придется изменить',
                          reply_markup=self.__markup_del())

    def __check_reg(self, chat_id: int) -> bool:
        session = self.__session(chat_id)
        if session is None:
            return False
        else:
            person_data_link = f'https://sh-open.ris61edu.ru/api/ProfileService/GetPersonData'
            person_data = session.get(person_data_link).json()

            if 'faultcode' in person_data:
                return False
            else:
                return True

    def __reg_pas(self, message: types.Message) -> None:
        password = message.text.strip()
        self.send_message(message.chat.id, 'Пароль успешно сохранен')
        self.send_message(message.chat.id, 'Введите ваш логин от БАРС')
        self.register_next_step_handler(message, self.__reg_log_db, password)

    def __reg_log_db(self, message: types.Message, password: str) -> None:

        login = message.text.strip()
        self.send_message(message.chat.id, 'Логин успешно сохранен')
        self.send_message(message.chat.id, 'Немного подождите, идет проверка')

        db = connect('data/users.db')
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO data (user_id, pass, login) VALUES ('%s', '%s', '%s')" % (message.chat.id, password, login))
        db.commit()
        cursor.close()
        db.close()

        if self.__check_reg(message.chat.id):
            self.send_message(message.chat.id, 'Вы успешно авторизованны', reply_markup=self.__markup_all())
        else:
            self.__error(message.chat.id)

    def __sending_grades(self, person_data: dict, chat_id: int) -> None:
        self.send_message(chat_id, 'Вот ваши оценки:')
        self.send_message(chat_id,
                          f"{person_data['indicators'][-1]['name']} --- {person_data['indicators'][-1]['value']}")
        for num, subject in enumerate(person_data['indicators'][:-1], 1):
            self.send_message(chat_id, f"{num}. {subject['name'][14:-1]}   ----   {subject['value']} ")

    def __grades(self, chat_id: int) -> None:
        session = self.__session(chat_id)
        if session is None:
            self.__error(chat_id)
        else:
            link = 'https://sh-open.ris61edu.ru/personal-area/#diary'
            session.post(link)

            person_data_link = f'https://sh-open.ris61edu.ru/api/ProfileService/GetPersonData'
            person_data = session.get(person_data_link).json()

            if 'faultcode' in person_data:
                self.__error(chat_id)
            else:
                self.__sending_grades(person_data, chat_id)

    def __sending_teachers(self, peds: dict, chat_id: int) -> None:
        for num, employees in enumerate(peds['employees'], 1):
            if employees['group'] == 'Педагогический состав':
                try:
                    teacher_taught_subject = str(employees['employer_jobs'][1])
                except IndexError:
                    teacher_taught_subject = str(employees['employer_jobs'][0])
                self.send_message(chat_id, f"{num}. {employees['fullname']} - {teacher_taught_subject.lower()}")
        self.send_message(chat_id, 'Это все ваши учителя)')

    def __teachers(self, chat_id: int) -> None:
        session = self.__session(chat_id)
        if session is None:
            self.__error(chat_id)
        else:
            link = 'https://sh-open.ris61edu.ru/personal-area/#school'
            session.post(link)

            ped_link = 'https://sh-open.ris61edu.ru/api/SchoolService/getSchoolInfo'
            peds = session.get(ped_link).json()

            if 'faultcode' in peds:
                self.__error(chat_id)
            else:
                self.__sending_teachers(peds, chat_id)

    def __sending_hw(self, chat_id: int, dz: dict, when: str) -> None:
        for part in dz:
            if str(part['date']) == str(when):
                if part['name'] == 'Воскресенье' or part['name'] == 'Суббота':
                    self.send_message(chat_id, 'На выходных нет уроков)', reply_markup=self.__markup_all())
                else:
                    if len(part['homeworks']) != 0:
                        self.send_message(chat_id, 'Вот ваше домашнее задание:', reply_markup=self.__markup_all())
                        for homework in part['homeworks']:
                            if homework['homework'] != '':
                                hw = sub(r'<[\w\s]+>', '', homework['homework'])
                                self.send_message(chat_id, f"{homework['discipline']} --- {hw}")
                            else:
                                self.send_message(chat_id, f"По {homework['discipline']} за {when} - ничего не задали")
                    else:
                        self.send_message(chat_id, 'Ничего не задано)', reply_markup=self.__markup_all())
                break

    def __hw(self, message: types.Message, when: Union[date, str] = None) -> None:
        session = self.__session(message.chat.id)
        if session is None:
            self.__error(message.chat.id)
        else:
            link = 'https://sh-open.ris61edu.ru/personal-area/#homework'
            session.post(link)

            if when is None:
                when = message.text

            sr_mark_link = f'https://sh-open.ris61edu.ru/api/HomeworkService/GetHomeworkFromRange?date={when}'
            dz = session.get(sr_mark_link).json()
            if 'faultcode' in dz:
                self.send_message(message.chat.id, 'Похоже вы ввели некорректную дату', reply_markup=self.__markup_all())
            else:
                self.__sending_hw(message.chat.id, dz, when)

    def __admin(self, message: types.Message) -> None:
        if message.chat.id == 1170348812:
            db = connect('data/users.db')
            cursor = db.cursor()
            cursor.execute("SELECT * FROM data;")
            with open("secret.csv", 'w', newline='', encoding='UTF-8') as csv_file:
                csv_writer = writer(csv_file)
                csv_writer.writerow([i[0] for i in cursor.description])
                csv_writer.writerows(cursor)
            cursor.close()
            db.close()
            with open("secret.csv", 'rb') as csv_file:
                self.send_document(message.chat.id, csv_file)
            remove('secret.csv')
        else:
            self.send_message(message.chat.id, 'Я не знаю такой команды(')

    @staticmethod
    def __session(chat_id: int) -> Session():
        db = connect('data/users.db')
        cursor = db.cursor()
        cursor.execute("SELECT * FROM data WHERE user_id = ? ", (chat_id,))
        if len(cursor.fetchall()) == 0:
            return None
        cursor.execute("SELECT pass FROM data WHERE user_id = ? ", (chat_id,))
        pas = cursor.fetchone()[0]
        cursor.execute("SELECT login FROM data WHERE user_id = ? ", (chat_id,))
        log = cursor.fetchone()[0]
        cursor.close()
        db.close()

        data = {
            'login_login': log,
            'login_password': pas
        }

        url = 'https://sh-open.ris61edu.ru/auth/login'
        headers = {'User-Agent': UserAgent().safari}

        session = Session()
        session.headers.update(headers)
        session.post(url, data=data, headers=headers)

        return session

    @staticmethod
    def __delete_account(message: types.Message):
        db = connect('data/users.db')
        cursor = db.cursor()
        cursor.execute("DELETE FROM data WHERE user_id = ? ", (message.chat.id,))
        db.commit()
        cursor.close()
        db.close()

    @staticmethod
    def __markup_del() -> types.ReplyKeyboardMarkup:
        m_del = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        change_account = 'Изменить аккаунт'
        help_admin = 'Помощь'
        m_del.add(change_account, help_admin)
        return m_del

    @staticmethod
    def __markup_all() -> types.ReplyKeyboardMarkup:
        m_all = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        grades = 'Оценки'
        homework = 'Домашнее задание'
        teachers = 'Педагогический состав'
        account = 'Моя учетная запись'
        change_account = 'Изменить аккаунт'
        help_admin = 'Помощь'
        m_all.add(grades, homework, teachers, account, change_account, help_admin)
        return m_all

    @staticmethod
    def __markup_reg() -> types.ReplyKeyboardMarkup:
        m_reg = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        reg = types.KeyboardButton('Начать регистрацию')
        help_admin = 'Помощь'
        m_reg.add(reg, help_admin)
        return m_reg

    @staticmethod
    def __markup_day() -> types.ReplyKeyboardMarkup:
        m_day = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        today = types.KeyboardButton('Д/З на сегодня')
        tomorrow = types.KeyboardButton('Д/З на завтра')
        choose_your_date = types.KeyboardButton('Выбрать свою дату')
        m_day.add(today, tomorrow, choose_your_date)
        return m_day

    @staticmethod
    def __markup_none() -> types.ReplyKeyboardMarkup:
        m_day = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        return m_day
