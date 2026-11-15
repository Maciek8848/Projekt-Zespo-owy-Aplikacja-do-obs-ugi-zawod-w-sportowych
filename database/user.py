from . import _admin
from ._admin import statusCode
import sqlite3

def add(login:str, password:str) -> statusCode:
    login = _admin.parseStr(login)
    password = _admin.parseStr(password)

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    retCode = statusCode.SUCCESS
    try:
        cursor.execute(
            "INSERT INTO user (login, password, name) VALUES (?, ?, ?)",
            (login, password, login)
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if not e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE": raise
        retCode = statusCode.EXIT

    conn.close()

    return retCode

def getId(login:str) -> int:
    login = _admin.parseStr(login)
    return _admin.getId("user", "login", login)

def get(ids:list[int]|None, login:bool=True, name:bool=True) -> list:
    colm=[]
    if(login): colm.append("login")
    if(name): colm.append("name")
    return _admin.get("user", ids, colm)

def delete(id:int) -> statusCode:
    return _admin.delete("user", id)

def alter(id:int, newLogin:str=None, newPassword:str=None, newName:str=None) -> statusCode:
    updates = []
    values = []

    if newLogin is not None:
        updates.append("login = ?")
        values.append(_admin.parseStr(newLogin))

    if newPassword is not None:
        updates.append("password = ?")
        values.append(_admin.parseStr(newPassword))

    if newName is not None:
        updates.append("name = ?")
        values.append(_admin.parseStr(newName))

    if len(values) == 0: return statusCode.SUCCESS

    return _admin.alter("user", id, updates, values)

def verify(login:str, password:str) -> tuple[bool, statusCode]:
    login = _admin.parseStr(login)
    password = _admin.parseStr(password)

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    retCode = statusCode.SUCCESS
    retStat = False
    try:
        cursor.execute(
            "SELECT password from user WHERE login=?",
            (login,)
        )

        userData = cursor.fetchone()
        if userData: 
            retStat = password == userData[0]
        else:
            retCode = statusCode.NOT_EXIT

    except Exception as e:
        print(e)

    conn.close()

    return retStat, retCode

