#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on: 12.02.2019 by Tunc Ali Kütükcüoglu
"""
Modify tables of database to make them 
more understandable and slimmer for students
"""
# import
import psycopg2
import sys, os, time

from CentralParameters import *
#*********************************************************************************
# parameters
#*********************************************************************************
FieldNamesToBeChangesInTimetableTable = {
	'haltestelle_ab': 'station_from',
	'haltestelle_an': 'station_to',

	'fahrt_id': 'travel_id',
	'id_fahrt_kopfzeile': 'travel_id_headerline',

	'hst_order': 'station_order',
	'fahrtnum': 'travel_no',
	'verwaltung': 'management',
	'gattung': 'line_category',
	'linie': 'line',
	'linie_id': 'line_id',

	'abfahrt_std': 'departure_hour',
	'abfahrt_min': 'departure_min',
	'abfahrtm': 'departure_totalmin',

	'ankunft_std': 'arrival_hour',
	'ankunft_min': 'arrival_min',
	'ankunftm': 'arrival_totalmin',

	'verkehrstage_bitfeld': 'trafficdays_bitfield',
	'verkehrstage_hexcode': 'trafficdays_hexcode'
}

FieldsToBeDeletedInTimetableTable = ['line_id_nr', 'richtung', 'verkehrstage_bitfeld_nummer', 'wochentage','wtagtyp']

# other line categories (Gattung) not included in this list will be deleted from timetable
LineCategoriesInTimetable = ['S','IC','ICE','IR','IRE','R','RE']

TablesToBeDeleted = ['gleise', 'umsteigezeit_metabhf', 'umsteigezeit_umsteigb']

TablesToBeRenamed = {
	'fahrt_kopfzeile': 'travel_headerline',
	'haltestellen_hafas': 'stations_hafas',
}

#*********************************************************************************
# start
#*********************************************************************************
print "-------------- START " + str(os.path.basename(__file__)) + " --------------"

# connect to database
dbcon = psycopg2.connect(**PrimaryDB) 
dbcur = dbcon.cursor()

# test database connection
dbcur.execute('SELECT version()')          
vers = dbcur.fetchone()
print vers 

# change field names (if field name exists)
print "\nChange field names in table timetable..."

for fname in FieldNamesToBeChangesInTimetableTable:
	new_name = FieldNamesToBeChangesInTimetableTable[fname]

	# check if field exists in table
	sql = "select column_name from information_schema.columns " \
		+ "WHERE table_name='timetable' and column_name='%s';" % fname
	dbcur.execute(sql)

	if dbcur.fetchone():
		print "field name %s found, rename to %s" % (fname, new_name)
		sql = "alter table timetable rename %s to %s" % (fname, new_name)
		dbcur.execute(sql)
		dbcon.commit()
	else:
		print "field name %s NOT found!" % fname

# delete fields (if field name exists)
print "\nDelete fields in table timetable..."

for fname in FieldsToBeDeletedInTimetableTable:

	# check if field exists in table
	sql = "select column_name from information_schema.columns " \
		+ "WHERE table_name='timetable' and column_name='%s';" % fname
	dbcur.execute(sql)

	if dbcur.fetchone():
		print "field %s found, delete field..." % fname
		sql = "alter table timetable drop column %s" % fname
		dbcur.execute(sql)
		dbcon.commit()
	else:
		print "field %s NOT found!" % fname

# delete entries with excluded line categories from timetable 
print "\nDelete entries with excluded line categories from timetable..."

condstr = "('" + "','".join(LineCategoriesInTimetable) + "')"
sql = "delete from timetable where line_category not in %s" % condstr
dbcur.execute(sql)
rows_deleted = dbcur.rowcount 
print "%s rows in timetable are deleted." % rows_deleted
dbcon.commit()

# delete tables
print "Delete tables..."
for table in TablesToBeDeleted:
	dbcur.execute("DROP TABLE IF EXISTS %s" % table)
dbcon.commit()

# rename tables
print "Rename tables..."
# see: http://www.postgresqltutorial.com/postgresql-rename-table/

for table in TablesToBeRenamed:
	ntable = TablesToBeRenamed[table]
	dbcur.execute("ALTER TABLE IF EXISTS %s RENAME TO %s" % (table, ntable))
dbcon.commit()

dbcur.close()
dbcon.close()
