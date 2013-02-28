-- Creates tables for homebrew gps repository.
-- Tables:
-- users
-- files
-- trackpoints
-- tracklines

PRAGMA foreign_keys=OFF;

BEGIN TRANSACTION;

CREATE TABLE users (
user_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
username TEXT NOT NULL,
UNIQUE (username));

INSERT INTO 'users' VALUES (1,'Daniel');
INSERT INTO 'users' VALUES (2,'Sophia');

CREATE TABLE files (
file_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
filename TEXT NOT NULL,
md5hash TEXT NOT NULL,
date_entered TEXT NOT NULL,
first_timestamp TEXT NOT NULL,
last_timestamp TEXT NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
UNIQUE (md5hash));

CREATE TABLE trackpoints (
trkpt_uid INTEGER PRIMARY KEY AUTOINCREMENT,
--track_id INTEGER,
trkseg_id INTEGER,
trksegpt_id INTEGER,
ele DOUBLE NOT NULL,
utctimestamp TEXT NOT NULL,
--name TEXT,
cmt TEXT,
--desc TEXT,
course DOUBLE,
speed DOUBLE,
file_uid INTEGER UNSIGNED NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
citydef_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (file_uid)
REFERENCES file (file_uid),
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid),
FOREIGN KEY (citydef_uid)
REFERENCES citydefs (citydef_uid),
UNIQUE (utctimestamp, user_uid));

SELECT AddGeometryColumn('trackpoints', 'geom', 4326, 'POINT', 'XY');
SELECT CreateSpatialIndex('trackpoints', 'geom');

-- CREATE TRIGGER "ggi_trackpoints_geom" BEFORE INSERT ON "trackpoints"
-- FOR EACH ROW BEGIN
-- SELECT RAISE(ROLLBACK, '"trackpoints"."geom" violates Geometry constraint [geom-type or SRID not allowed]')
-- WHERE (SELECT type FROM geometry_columns
-- WHERE f_table_name = 'trackpoints' AND f_geometry_column = 'geom'
-- AND GeometryConstraints(NEW."geom", type, srid, 'XY') = 1) IS NULL;
-- END;

CREATE TABLE tracklines (
trkline_uid INTEGER PRIMARY KEY AUTOINCREMENT,
trkseg_id INTEGER,
name TEXT,
--cmt TEXT,
--desc TEXT,
timestamp_start TEXT NOT NULL,
timestamp_end TEXT NOT NULL,
--link TEXT,
--type TEXT,
length_m DOUBLE,
time_sec DOUBLE,
speed_kph DOUBLE,
--points INTEGER,
file_uid INTEGER UNSIGNED NOT NULL,
user_uid INTEGER UNSIGNED NOT NULL,
FOREIGN KEY (file_uid)
REFERENCES file (file_uid),
FOREIGN KEY (user_uid)
REFERENCES users (user_uid),
FOREIGN KEY (trkseg_id)
REFERENCES tracksegments (trkseg_uid),
UNIQUE (timestamp_start, user_uid, trkseg_id)
);

SELECT AddGeometryColumn('tracklines', 'geom', 4326, 'LINESTRING', 'XY');
SELECT CreateSpatialIndex('tracklines', 'geom');

-- CREATE TRIGGER "ggi_tracklines_geom" BEFORE INSERT ON "tracklines"
-- FOR EACH ROW BEGIN
-- SELECT RAISE(ROLLBACK, '"tracklines"."geom" violates Geometry constraint [geom-type or SRID not allowed]')
-- WHERE (SELECT type FROM geometry_columns
-- WHERE f_table_name = 'tracklines' AND f_geometry_column = 'geom'
-- AND GeometryConstraints(NEW."geom", type, srid, 'XY') = 1) IS NULL;
-- END;

CREATE TABLE citydefs (
citydef_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
city TEXT NOT NULL,
country TEXT NOT NULL,
UNIQUE(city, country)
);

SELECT AddGeometryColumn('citydefs', 'geom', 4326, 'POLYGON', 'XY');
SELECT CreateSpatialIndex('citydefs', 'geom');

CREATE TABLE tracksegments (
trkseg_uid INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
trkseg_uuid TEXT NOT NULL,
UNIQUE(trkseg_uuid)
);

COMMIT;
