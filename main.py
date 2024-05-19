from bot import TgBot
from sqlite3 import connect


def main() -> None:
    """
    Основная функция программы. Открывает файл с токеном,
    подключается к базе данных,
    создает таблицу для хранения данных пользователей, если она еще не создана, и запускает бота.

    :return: None
    """
    with open('token', 'r') as file:
        token: str = file.read()

    db = connect('data/users.db')
    cursor = db.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS data (
                    user_id varchar(50),
                    pass varchar(50),
                    login varchar(50)
                )""")
    db.commit()
    cursor.close()
    db.close()

    bot: TgBot = TgBot(token)
    bot.run()


if __name__ == "__main__":
    """
    Этот блок if проверяет, был ли этот файл вызван напрямую или он был импортирован другим модулем.
    Если имя модуля равно "main", это означает, что файл был вызван напрямую. В этом случае вызывается функция main().

    :return: None
    """
    main()
