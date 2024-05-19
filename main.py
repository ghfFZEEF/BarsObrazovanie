from bot import TgBot
from sqlite3 import connect


def main() -> None:
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
    main()
