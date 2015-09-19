CREATE DATABASE IF NOT EXISTS telega CHARACTER SET utf8;
GRANT ALL ON telega.* TO 'telega'@'localhost' IDENTIFIED BY 'hJuRJkWhR1';
USE telega;

CREATE TABLE IF NOT EXISTS Channels (
    id INT NOT NULL AUTO_INCREMENT,
    name TINYTEXT NOT NULL,
    button SMALLINT NOT NULL,
    link TINYTEXT NOT NULL,
    known_until DATE DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS Filters (
    id INT NOT NULL AUTO_INCREMENT,
    title TEXT NOT NULL,
    deleting ENUM('+') DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS Heuristics (
    id INT NOT NULL AUTO_INCREMENT,
    type TINYTEXT NOT NULL,
    genre TINYTEXT NOT NULL,
    year TINYTEXT NOT NULL,
    country TINYTEXT NOT NULL,
    deleting ENUM('+') DEFAULT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS Events (
    id INT NOT NULL AUTO_INCREMENT,
    begin DATETIME NOT NULL,
    end DATETIME,
    title TEXT NOT NULL,
    link TINYTEXT NOT NULL,
    channel_id INT NOT NULL,
    state ENUM('filter', 'heuristic') DEFAULT NULL,
    filter_id INT DEFAULT NULL,
    heuristic_id INT DEFAULT NULL,
    FOREIGN KEY (channel_id) REFERENCES Channels(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (filter_id) REFERENCES Filters(id)
        ON UPDATE CASCADE,
    FOREIGN KEY (heuristic_id) REFERENCES Heuristics(id)
        ON UPDATE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS EventInfo (
    id INT NOT NULL AUTO_INCREMENT,
    type TINYTEXT NOT NULL,
    genre TINYTEXT NOT NULL,
    year TINYTEXT NOT NULL,
    country TINYTEXT NOT NULL,
    event_id INT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES Events(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS Tasks (
    id INT NOT NULL AUTO_INCREMENT,
    time TIMESTAMP NOT NULL,
    processor TINYTEXT NOT NULL,
    target_id INT DEFAULT NULL,
    PRIMARY KEY (id)
);
