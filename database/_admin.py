import sqlite3
import os
from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
databaseName = BASE_DIR / "database.db"

class statusCode(Enum):
    SUCCESS=0
    FAIL=1
    EXIT=2
    NOT_EXIT=3

# databaseName = "./database/database.db"

def parseStr(s: str) -> str:
    if not isinstance(s, str): raise TypeError("musi być typ str")
    s = s.strip()
    if not s: raise TypeError("str nie mogą być tylko spacje")
    return s

def reset() -> None:
    if os.path.exists(databaseName):
        os.remove(databaseName)
    
    conn = sqlite3.connect(databaseName)

    with open(BASE_DIR / "db_init.sql") as f:
        conn.executescript(f.read())
    
    conn.commit()
    conn.close()

def printTalble(name:str, cursor:sqlite3.Cursor):
    cursor.execute(f"SELECT * FROM {name}")
    rows = cursor.fetchall()
    print(name)
    for row in rows:
        print(row)

def printAll():
    conn = sqlite3.connect(databaseName)
    cursor = conn.cursor()

    printTalble("user",cursor)
    printTalble("team",cursor)
    printTalble("team_user",cursor)

    conn.commit()
    conn.close()

# print(__name__)

if __name__ == "__main__":
    printAll()
    reset()