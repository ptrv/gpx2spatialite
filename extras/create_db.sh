#! /bin/sh

spatialite $1 ".read create_db.sql utf-8"
spatialite $1 ".read insert_citydefs.sql utf-8"
