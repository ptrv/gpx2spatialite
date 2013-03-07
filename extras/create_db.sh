#! /bin/sh

if [ $# -ne 1 ]
then 
    echo "Please pass a database name to the script"
    echo "e.g. create_db.sh newdb.sqlite"
    exit 2
fi

spatialite $1 ".read create_db.sql utf-8"
spatialite $1 ".read insert_citydefs.sql utf-8"
