# - *- coding: utf- 8 - *-
import random
import sqlite3
import time
from sqlite3 import IntegrityError
import config

# Путь к БД

####################################################################################################
###################################### ФОРМАТИРОВАНИЕ ЗАПРОСА ######################################
# Форматирование запроса с аргументами
def update_format_with_args(sql, parameters: dict):
    values = ", ".join([
        f"{item} = ?" for item in parameters
    ])
    sql = sql.replace("XXX", values)
    return sql, tuple(parameters.values())


# Форматирование запроса без аргументов
def get_format_args(sql, parameters: dict):
    sql += " AND ".join([
        f"{item} = ?" for item in parameters
    ])
    return sql, tuple(parameters.values())


####################################################################################################
########################################### ЗАПРОСЫ К БД ###########################################
# Добавление данных в таблицы
def add_accounts(account_data, category_name):
    try:
        with sqlite3.connect(config.path_to_db) as db:
            db.execute("INSERT INTO accounts "
                       "(account_data, category_name) "
                       "VALUES (?, ?)",
                       [account_data, category_name])
            db.commit()
    except sqlite3.IntegrityError:
        pass


def get_all_accounts():
    with sqlite3.connect(config.path_to_db) as db:
        sql = "SELECT * FROM accounts "
        return db.execute(sql).fetchall()


def update_accounts(id, **kwargs):
    with sqlite3.connect(config.path_to_db) as db:
        sql = f"UPDATE accounts SET XXX WHERE id = {id}"
        sql, parameters = update_format_with_args(sql, kwargs)
        db.execute(sql, parameters)
        db.commit()


def delete_accounts(**kwargs):
    with sqlite3.connect(config.path_to_db) as db:
        sql = "DELETE FROM accounts WHERE "
        sql, parameters = get_format_args(sql, kwargs)
        db.execute(sql, parameters)
        db.commit()




