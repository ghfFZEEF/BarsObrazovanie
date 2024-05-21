from bot import TgBot
from sqlite3 import connect, Connection, Cursor
import json


def main() -> None:
    """
    Основная функция программы. Открывает файл с токеном,
    подключается к базе данных,
    создает таблицу для хранения данных пользователей, если она еще не создана, и запускает бота.

    :return: None
    """
    with open('token.json', 'r') as file:
        data: dict = json.load(file)

    db: Connection = connect('data/users.db')
    cursor: Cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS data (
                    user_id varchar(50),
                    pass varchar(50),
                    login varchar(50)
                )""")
    db.commit()
    cursor.close()
    db.close()

    bot: TgBot = TgBot(data["token"])
    bot.run()


if __name__ == "__main__":
    """
    Этот блок if проверяет, был ли этот файл вызван напрямую или он был импортирован другим модулем.
    Если имя модуля равно "main", это означает, что файл был вызван напрямую. В этом случае вызывается функция main().

    :return: None
    """
    main()
