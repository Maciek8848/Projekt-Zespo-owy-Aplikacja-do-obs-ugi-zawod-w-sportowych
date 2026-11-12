PRAGMA foreign_keys = ON;

CREATE TABLE user (
    id       INTEGER PRIMARY KEY,
    login    TEXT UNIQUE,
    password TEXT,
    name     TEXT
);

CREATE TABLE team (
    id      INTEGER PRIMARY KEY,
    name    TEXT UNIQUE
);

CREATE TABLE team_user (
    id_user   INTEGER,
    id_team   INTEGER,
    permition INTEGER not NULL,
    FOREIGN KEY(id_user) REFERENCES user(id)
    FOREIGN KEY(id_team) REFERENCES team(id)
    UNIQUE (id_user, id_team)
);

CREATE TRIGGER delete_team
AFTER DELETE ON team
FOR EACH ROW
BEGIN
    DELETE FROM team_user
    WHERE id_team = OLD.id;
END;

CREATE TRIGGER delete_user
AFTER DELETE ON user
FOR EACH ROW
BEGIN
    DELETE FROM team_user
    WHERE id_user = OLD.id;
END;