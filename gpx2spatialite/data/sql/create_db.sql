-- Creates tables for homebrew gps repository.
-- Tables:
-- users
-- files
-- trackpoints
-- tracklines

PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TABLE users (
user_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
UNIQUE (username));

CREATE TABLE files (
file_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
filename TEXT NOT NULL,
md5hash TEXT NOT NULL,
date_entered TEXT NOT NULL,
first_timestamp TEXT,
last_timestamp TEXT,
user_uid INTEGER NOT NULL,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
UNIQUE (md5hash));

CREATE TABLE trackpoints (
trkpt_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
trkseg_id INTEGER,
trksegpt_id INTEGER,
ele REAL NOT NULL,
utctimestamp TEXT NOT NULL,
comment TEXT,
course REAL,
speed REAL,
file_uid INTEGER NOT NULL,
user_uid INTEGER NOT NULL,
citydef_uid INTEGER,
FOREIGN KEY (file_uid)
REFERENCES files (file_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (citydef_uid)
REFERENCES citydefs (citydef_uid),
UNIQUE (utctimestamp, user_uid));

SELECT AddGeometryColumn('trackpoints', 'geom', 4326, 'POINT', 'XY', 1);
SELECT CreateSpatialIndex('trackpoints', 'geom');

CREATE TABLE tracklines (
trkline_uid INTEGER PRIMARY KEY AUTOINCREMENT,
trkseg_id INTEGER,
comment TEXT,
timestamp_start TEXT NOT NULL,
timestamp_end TEXT NOT NULL,
length_m REAL,
time_sec REAL,
speed_kph REAL,
file_uid INTEGER NOT NULL,
user_uid INTEGER NOT NULL,
FOREIGN KEY (file_uid)
REFERENCES files (file_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid) ON DELETE CASCADE ON UPDATE CASCADE,
UNIQUE (timestamp_start, user_uid, trkseg_id)
);

SELECT AddGeometryColumn('tracklines', 'geom', 4326, 'LINESTRING', 'XY', 1);
SELECT CreateSpatialIndex('tracklines', 'geom');

CREATE TABLE citydefs (
citydef_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
city TEXT NOT NULL,
country TEXT NOT NULL,
UNIQUE(city, country)
);

SELECT AddGeometryColumn('citydefs', 'geom', 4326, 'POLYGON', 'XY', 1);
SELECT CreateSpatialIndex('citydefs', 'geom');

CREATE TABLE tracksegments (
trkseg_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
trkseg_uuid TEXT NOT NULL,
UNIQUE(trkseg_uuid)
);

CREATE TABLE waypoints (
wpt_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
wpt_name TEXT,
ele REAL,
utctimestamp TEXT,
sym TEXT,
file_uid INTEGER,
user_uid INTEGER,
citydef_uid INTEGER,
FOREIGN KEY (file_uid)
REFERENCES files (file_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid) ON DELETE CASCADE ON UPDATE CASCADE,
FOREIGN KEY (citydef_uid)
REFERENCES citydefs (citydef_uid));

SELECT AddGeometryColumn('waypoints', 'geom', 4326, 'POINT', 'XY', 1);
SELECT CreateSpatialIndex('waypoints', 'geom');

COMMIT;
