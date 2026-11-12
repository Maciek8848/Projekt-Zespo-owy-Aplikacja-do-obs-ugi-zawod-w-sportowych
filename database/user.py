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

def delete(id:int) -> statusCode:
    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    retCode = statusCode.SUCCESS
    try:
        cursor.execute(
            "DELETE FROM user WHERE id=?",
            (id,)
        )

        if cursor.rowcount == 0:
            retCode = statusCode.NOT_EXIT
        elif cursor.rowcount > 1:
            raise Exception("były duplikaty, jakoś")

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

    conn.close()

    return retCode

def alter(id:int, newLogin:str=None, newPassword:str=None, newName:str=None) -> statusCode:
    # login = _admin.parseStr(login)

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

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    query = f"UPDATE user SET {','.join(updates)} WHERE id=?"
    values.append(id)
    retCode = statusCode.SUCCESS
    try:
        cursor.execute(query, values)
        if cursor.rowcount == 0:
            retCode = statusCode.NOT_EXIT
        elif cursor.rowcount > 1:
            raise Exception("były duplikaty, jakoś")
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if not e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE": raise
        retCode = statusCode.EXIT
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()

    return retCode

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

def getId(login:str) -> int:
    login = _admin.parseStr(login)

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    query = f"SELECT id FROM user WHERE login=?"
    cursor.execute(query, (login,))
    data = cursor.fetchone()

    conn.close()

    if(data is None): return None
    return data[0]

def get(ids:list[int], login:bool=True, name:bool=True) -> list:
    find = []
    values = []
    
    for i in ids:
        find.append("?")
        values.append(i)
        # logins[i] = _admin.parseStr(logins[i])
    
    colm = ["id"]
    if(login): colm.append("login")
    if(name): colm.append("name")

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    query = f"SELECT {','.join(colm)} FROM user WHERE id in ({','.join(find)})"

    cursor.execute(query, values)
    data = cursor.fetchall()

    conn.close()

    return data

# reset()