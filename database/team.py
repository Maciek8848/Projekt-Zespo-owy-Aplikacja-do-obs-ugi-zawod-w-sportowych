from . import _admin
from ._admin import statusCode
from . import user
import sqlite3
from enum import Enum

class permition(Enum):
    NONE = 0
    EDIT = 1
    OWNER = 2

def add(name:str, owner_id:int) -> statusCode:
    name = _admin.parseStr(name)

    conn = sqlite3.connect(_admin.databaseName)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    retCode = statusCode.SUCCESS
    try:
        cursor.execute(
            "INSERT INTO team (name) VALUES (?)",
            (name,)
        )
        id_team = cursor.lastrowid

        cursor.execute(
            "INSERT INTO team_user (id_user, id_team, permition) VALUES (?,?,?)",
            (owner_id, id_team, permition.OWNER.value)
        )

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE": retCode = statusCode.EXIT
        elif e.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY": retCode = user.statusCode.NOT_EXIT
        else: raise
    finally:
        conn.close()

    return retCode

def getId(name:str) -> int:
    name = _admin.parseStr(name)
    return _admin.getId("team", "name", name)

def get(ids:list[int]|None, name:bool=True) -> list:
    colm=[]
    if(name): colm.append("name")
    return _admin.get("team", ids, colm)

def delete(id:int) -> statusCode:
    return _admin.delete("team", id)

def alter(id:int, newName:str = None) -> statusCode:
    updates = []
    values = []

    if newName is not None:
        updates.append("name = ?")
        values.append(_admin.parseStr(newName))

    if len(values) == 0: return statusCode.SUCCESS

    return _admin.alter("team", id, updates, values)

def add_user(id_team:int, id_user:list[int]) -> statusCode:
    conn = sqlite3.connect(_admin.databaseName)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    row = []
    values = []
    for id in id_user:
        row.append(f"(?,?, {permition.NONE.value})")
        values.append(id)
        values.append(id_team)

    query = f"INSERT INTO team_user (id_user, id_team, permition) VALUES {','.join(row)}"

    retCode = statusCode.SUCCESS
    try:
        cursor.execute(query, values)
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if e.sqlite_errorname == "SQLITE_CONSTRAINT_FOREIGNKEY": retCode = statusCode.NOT_EXIT
        elif e.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE": retCode = statusCode.EXIT
        else: raise
    finally:
        conn.close()

    return retCode

def del_user(id_team:int, id_user:list[int]) -> statusCode:
    row = []
    values = []

    for id in id_user:
        row.append("?")
        values.append(id)
    values.append(id_team)

    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    query = f"DELETE FROM team_user WHERE id_user in ({','.join(row)}) and id_team=?"
    cursor.execute(query, values)
    conn.commit()

    conn.close()

    return statusCode.SUCCESS

def get_allUser(id_team:int) -> list[int]:
    conn = sqlite3.connect(_admin.databaseName)
    cursor = conn.cursor()

    query = "SELECT id_user FROM team_user WHERE id_team=?"
    cursor.execute(query, (id_team,))
    data = [i[0] for i in cursor.fetchall()]

    conn.close()

    return data