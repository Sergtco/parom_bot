import sqlite3 as sql


class Database:
    def __init__(self, name="users.db"):
        self.name = name
        self.__con = sql.connect(name, check_same_thread=False)
        self.cur = self.__con.cursor()
        exists = self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user'"
        )
        if exists.fetchone() is None:
            self.cur.execute(
                "CREATE TABLE user(tg_id INTEGER, period INTEGER, date INTEGER)"
            )

    def add(self, tg_id: int, period: int, date: int):
        exists = self.cur.execute(
            f"SELECT EXISTS (SELECT 1 FROM user WHERE tg_id = {tg_id})"
        )
        if exists != 1:
            self.cur.execute(
                f"INSERT INTO user (tg_id, period, date) VALUES ({tg_id}, {period}, {date})"
            )
        else:
            self.cur.execute(
                f"UPDATE user SET (period, date) = ({period}, {date}) WHERE tg_id = {tg_id}"
            )
        self.__con.commit()

    def delete(self, tg_id):
        self.cur.execute(f"DELETE FROM user WHERE tg_id = {tg_id}")
        self.__con.commit()

    def dump(self):
        res = self.cur.execute(
            "SELECT tg_id ,period, date FROM user"
        )
        return res.fetchall()

    def get(self, tg_id) -> tuple:
        period, date = self.cur.execute(
            f"SELECT period, date FROM user WHERE tg_id = {tg_id}"
        )
        return period, date
