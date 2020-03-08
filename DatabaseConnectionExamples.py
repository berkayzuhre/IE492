#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on: 12.02.2019 by Tunc Ali Kütükcüoglu
# https://software.tuncalik.com/
# see: http://initd.org/psycopg/docs/usage.html
"""
Examples demonstration Python-PostgreSQL connection
"""
# import
import psycopg2
import sys, os, time

from CentralParameters import *
#*********************************************************************************
# parameters
#*********************************************************************************


#*********************************************************************************
# start
#*********************************************************************************
print "-------------- START " + str(os.path.basename(__file__)) + " --------------"

# Connect to database
dbcon = psycopg2.connect("dbname=timetable2018_slim user=postgres password=nZ64mTET")
# alternative: dbcon = psycopg2.connect(**PrimaryDB) 

# Open a cursor to perform database operations
dbcur = dbcon.cursor()

# query database
sql = """
	select travel_id,station_order,management,line_category,
	line,station_from,station_to,departure_totalmin,arrival_totalmin,
	trafficdays_bitfield from timetable 
	where management=11 and line_category='S' and line='14' and travel_id=9748
	order by travel_id,station_order
	"""
print "\nExecute SQL %s..." % sql
dbcur.execute(sql)
selected_rows = dbcur.fetchall()

# Note: selected_rows is a list of N-tuples in python.

print "\nDisplay selected rows:"
for row in selected_rows:
	print row


print selected_rows[2]

# select only the first row
dbcur.execute(sql)
selected_row = dbcur.fetchone()
print "\nDisplay selected row:"
print selected_row

