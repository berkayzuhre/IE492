#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Tunc Ali Kütükcüoglu (on 24. Feb 2020)
# see: https://software.tuncalik.com/travel-and-assignment-planning-software-in-python/4812
# Copyrights: Tunc Ali Kütükcüoglu (senior data analyst & developer)
"""
Training script for handling routes:
- Find some routes to work with (simple travel planning)
- Line Measurement (LM) coverage of routes 
- Travel Segments
- Route Segments 
- Measurement Variants (Measurement Specifications)
"""
import psycopg2
import sys, os
import time
import math
from timeit import default_timer
from datetime import date 
from datetime import datetime
from datetime import timedelta
import calendar
import itertools as it

from BU2019_CentralParameters import *
from BU2019_BasicFunctionsLib import *
from BU2019_TourSearch import *
from BU2020_AssignmentFunctions import *

# **************************************************************************************
# start
# **************************************************************************************

# database connection
dbcon = psycopg2.connect(**PrimaryDB) 
dbcur = dbcon.cursor()

# read routes from saved variable if it exists
Read_RouteInfoList_FromFile = False  

# line separator string
LineSeparator = 100 * '*'

# **************************************************************************************
# define route conditions
RelevantLineCategories = ['RE','R','IR','IC','ICE','S']		# ['RE','R','IR','IC','ICE','S']
RelevantManagements = [11,33]

# initiate list of tours as global variable
RouteInfoList1 = None

# stations:
# 8507000: Bern
# 8503000: Zürich

# conditions for tour search
# Bern --> Zürich
RouteConditions1 = {
	# von und bis Haltestelle (mandatory condition)
	Cond.StartAndEndStations: (8503000, 8503000), 	
	
	# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
	# determines earliest and latest arrival to end station
	Cond.StartTimeAndDuration: (8, 0, 60, 120),		
	
	# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
	Cond.MaxWaitingTimeAtStation: (30,),			
	
	# Min nötige Umsteige-Zeit in Minuten (mandatory condition)
	Cond.TimeForLineChange: (2,),

	# Cond.IncludeListedGattungsOnly: (RelevantLineCategories,), 	
	Cond.IncludeListedManagementsOnly: (RelevantManagements,),			# [11,33,7000]

	# connection availability on given days
	Cond.ConnectionsAreAvailableOnAllListedDays: (GetWeekdaysOfMonth(PlanMonth, PlanYear, WD[11]),),

	# select/filter only earliest arrival routes 
	#True: minimum number of line changes as primary selection criterion
	# Cond.SearchRoutesForEarliestArrival: (False,),

	# Parameter: Reporting frequency in seconds
	Cond.ReportDuringRouteSearch: (10,), 

	# return routes found in x seconds
	Cond.MaxSearchTimeInSeconds: (10,),
	}

RelevantLineCategories = ['S']		# ['RE','R','IR','IC','ICE','S']

# conditions for tour search
# Bern --> Bern
RouteConditions2 = {
	# von und bis Haltestelle (mandatory condition)
	Cond.StartAndEndStations: (8503000, 8507000), 	
	
	# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
	# determines earliest and latest arrival to end station
	Cond.StartTimeAndDuration: (8, 0, 60, 120),		
	
	# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
	Cond.MaxWaitingTimeAtStation: (30,),			
	
	# Min nötige Umsteige-Zeit in Minuten (mandatory condition)
	Cond.TimeForLineChange: (2,),

	Cond.IncludeListedGattungsOnly: (RelevantLineCategories,), 	
	Cond.IncludeListedManagementsOnly: (RelevantManagements,),			# [11,33,7000]

	# connection availability on given days
	Cond.ConnectionsAreAvailableOnAllListedDays: (GetWeekdaysOfMonth(PlanMonth, PlanYear, WD[11]),),

	# max number of allowed line changes
	Cond.MaxNumberOfLineChanges: (4,),

	# Parameter: Reporting frequency in seconds
	Cond.ReportDuringRouteSearch: (10,), 

	# return routes found in x seconds
	Cond.MaxSearchTimeInSeconds: (30,),
	}


# **************************************************************************************

def TEST_ReadTimeTable():

	(TimeTableList, TimeTableIndex, StationHourIndex) = ReadTimeTable(dbcur, RouteConditions1)
	print "TimeTableList:"
	for line in TimeTableList:
		print line

def TEST_FindAndDisplayRoutes():
	"""
	if Read_RouteInfoList_FromFile = True AND a saved variable exists --> read tours from saved variable
	Otherwise, search tours and save results (i.e. list of tours, RouteInfoList1)
	"""
	global RouteInfoList1
	print "\nFind all routes for the given route conditions..."

	# search conditions to be used
	RouteConditions = RouteConditions1

	if Read_RouteInfoList_FromFile:
		RouteInfoList1 = ReadVariableFromFile(PlanYear, PlanMonth, 'RouteInfoList1', directory=VariableDirectory)
		if RouteInfoList1:
			print "\nRoutes were read from saved variable."
		else:
			print "\nThere is no saved variable for routes."
	
	if not Read_RouteInfoList_FromFile or not RouteInfoList1:
		print "\nFind routes for the given route conditions..."
		(RouteInfoList1, StatusReport, TerminationReasons) = FindAllRoutes(dbcur, RouteConditions)
		print 
		print "StatusReport: " + str(StatusReport)
		print "TerminationReasons: " + str(TerminationReasons)
		print "length of RouteInfoList1: %s" % len(RouteInfoList1)

		# save variable to file
		#SaveVariableToFile(RouteInfoList1, PlanYear, PlanMonth, 'RouteInfoList1', directory=VariableDirectory)

	N = 10

	print "\nDisplay first %s routes in RouteInfoList1" % N
	ctr = 0
	for RouteInfo in RouteInfoList1:
		ctr += 1 
		if ctr > N: break
		
		print "\nRoute-" + str(ctr)

		# print raw RouteInfo
		print "\nRaw RouteInfo:"
		for conn in RouteInfo:
			conn = list(conn)
			conn[ConnInfoInd['trafficdays_hexcode']] = '-'
			print tuple(conn)

		print "\nRouteInfo:"
		print PrettyStringRouteInfo(RouteInfo)

# test module
if __name__ == '__main__':
	# **************************************************************************************
	# Find Some Routes
	# **************************************************************************************
	print LineSeparator
	print "Simple Travel Planning to find some routes to work with"
	print LineSeparator

	TEST_FindAndDisplayRoutes() 

	print LineSeparator
	print "Evaluate tours"
	print LineSeparator

	print "RouteConditions1 is a list that contains %s routes." % len(RouteInfoList1)

	# **************************************************************************************
	# Line Measurement (LM) Coverage of Routes
	# **************************************************************************************
	print LineSeparator 
	print "Line Measurement (LM) Coverage of Routes"
	print LineSeparator

	# In order to calculate the Line Measurement (LM) coverage of a route,
	# we need to have first LMRequirementsAll per LineKey (LineID, TimeWindow, WeekdayGroup):
	LMRequirementsAll = {
		('7.S24c',2,11):   2,
		('7.S9a',2,11):   2,
		('2.RE4a',2,11):   2,
		('2.RE4b',2,11):   2,
		('1.RE1',2,11):   2,
		('2.RE3',2,11):   2,
		('2.R14',2,11):   2,
		('2.R13',2,11):   2,
		('6.S10',2,11):   2,
		('6.RE2',2,11):   2,
		('6.S2',2,11):   2,
		('5.RE1',2,11):   2,
		('8.RE1',2,11):   2,
		('1.S2a',2,11):   2,
		('1.S2b',2,11):   2,
		('2.R8',2,11):   2,
		('2.R12',2,11):   2,
		('2.R10',2,11):   2,
		('2.R9',2,11):   2,
		('2.R11',2,11):   2,
		('4.R6',2,11):   2,
		('4.R5',2,11):   2,
		('6.S23a',2,11):   2,
		('6.S23b',2,11):   2,
		('6.S25',2,11):   2,
		('6.S26',2,11):   2,
		('6.S27',2,11):   2,
		('5.S28',2,11):   2,
		('6.S29',2,11):   2,
		('1.R3',2,11):   2,
		('1.R4',2,11):   2,
		('2.S9',2,11):   2,
		('2.S1',2,11):   2,
		('1.S3b',2,11):   2,
		('2.S4b',2,11):   2,
		('1.S3a',2,11):   2,
		('2.S4a',2,11):   2,
		('2.S5b',2,11):   2,
		('2.S5a',2,11):   2,
		('1.S7',2,11):   2,
		('2.S8',2,11):   2,
		('2.S40',2,11):   2,
		('2.S30',2,11):   2,
		('5.S1',2,11):   2,
		('5.S3c',2,11):   2,
		('5.S3b',2,11):   2,
		('5.S9',2,11):   2,
		('5.S3a',2,11):   2,
		('7.S24b',2,11):   2,
		('7.S8a',2,11):   2,
		('7.S5b',2,11):   2,
		('7.S2b',2,11):   2,
		('7.S2a',2,11):   2,
		('7.S3a',2,11):   2,
		('7.S3b',2,11):   2,
		('7.S5a',2,11):   2,
		('7.S6a',2,11):   2,
		('7.S6b',2,11):   2,
		('7.S7a',2,11):   2,
		('7.S7b',2,11):   2,
		('7.S8b',2,11):   2,
		('7.S8c',2,11):   2,
		('7.S9b',2,11):   2,
		('7.S12b',2,11):   2,
		('6.S42',2,11):   2,
		('7.S12a',2,11):   2,
		('7.S14b',2,11):   2,
		('7.S14a',2,11):   2,
		('7.S15a',2,11):   2,
		('7.S15b',2,11):   2,
		('7.S16b',2,11):   2,
		('7.S16a',2,11):   2,
		('7.S19a',2,11):   2,
		('7.S19b',2,11):   2,
		('7.S21',2,11):   2,
		('7.S24a',2,11):   2,
		('7.S25',2,11):   2,
		('6.S1',2,11):   2,
		('5.S18',2,11):   2,
		('6.S3',2,11):   2,
		('6.S9',2,11):   2,
		('5.S8',2,11):   2,
		('8.S6',2,11):   2,
		('6.S41',2,11):   2,
		('6.S30',2,11):   2,
		('6.S20',2,11):   2,
		('4.R7',2,11):   2,
		('1.R11',2,11):   2,
		('4.R3',2,11):   2,
		('2.R5',2,11):   2,
		('3.R11',2,11):   2,
		('8.S23',2,11):   2,
		('8.S22',2,11):   2,
		('8.S24',2,11):   2,
		('8.S21',2,11):   2,
		('8.S25',2,11):   2,
		('8.S26',2,11):   2,
		('1.R14',2,11):   2,
		('1.R15',2,11):   2,
		('1.R13',2,11):   2,
		('1.R6',2,11):   2,
		('2.S50',2,11):   2,
		('2.S60',2,11):   2,
		('1.R20',2,11):   2,
		('6.S16',2,11):   2,
		('3.RE1a',2,11):   2,
		('3.RE1b',2,11):   2,
		('3.RE2a',2,11):   2,
		('3.RE2b',2,11):   2,
		('3.RE4',2,11):   2,
		('4.RE1',2,11):   2,
		('3.R4b',2,11):   2,
		('3.R4a',2,11):   2,
		('3.R2',2,11):   2,
		('3.R1',2,11):   2,
		('3.R5',2,11):   2,
		('3.R6',2,11):   2,
		('3.R7',2,11):   2,
		('3.S1a',2,11):   2,
		('3.S2a',2,11):   2,
		('3.S44a',2,11):   2,
		('3.S44c',2,11):   2,
		('3.S1b',2,11):   2,
		('3.S2b',2,11):   2,
		('3.S3a',2,11):   2,
		('3.S3b',2,11):   2,
		('3.S4b',2,11):   2,
		('3.S4a',2,11):   2,
		('3.S5',2,11):   2,
		('3.S6',2,11):   2,
		('3.S51',2,11):   2,
		('3.S52',2,11):   2,
		('3.S31a',2,11):   2,
		('3.S31b',2,11):   2,
		('3.S44b',2,11):   2,
		('4.S6b',2,11):   2,
		('4.S7',2,11):   2,
		('4.S6a',2,11):   2,
		('4.S61',2,11):   2,
		('3.R8',2,11):   2,
		('3.R9',2,11):   2,
		('7.R2',2,11):   2,
		('2.R1',2,11):   2,
		('1.R16',2,11):   2,
		('1.R10',2,11):   2,
		('2.R4',2,11):   2,
		('2.R3',2,11):   2,
		('2.R2',2,11):   2,
		('2.R6',2,11):   2,
		('7.S18',2,11):   2,
		('6.S60',2,11):   2,
		('1.R19',2,11):   2,
		('1.R17',2,11):   2,
		('6.R1',2,11):   2,
		('8.S15',2,11):   2,
		('2.RE2',2,11):   2,
		('2.S20',2,11):   2,
		('2.S21',2,11):   2,
		('1.R5',2,11):   2,
		('4.R2',2,11):   2,
		('1.R22',2,11):   2,
		('1.R7',2,11):   2,
		('1.R9',2,11):   2,
		('1.R8',2,11):   2,
		('8.S30',2,11):   2,
		('8.S8b',2,11):   2,
		('8.S8c',2,11):   2,
		('8.S7',2,11):   2,
		('8.S35',2,11):   2,
		('7.S22',2,11):   2,
		('7.S29',2,11):   2,
		('7.S41a',2,11):   2,
		('7.S41b',2,11):   2,
		('7.S33',2,11):   2,
		('7.S26',2,11):   2,
		('8.S55',2,11):   2,
		('8.R1',2,11):   2,
		('8.S1',2,11):   2,
		('8.S2',2,11):   2,
		('8.S3',2,11):   2,
		('8.S5',2,11):   2,
		('8.S8a',2,11):   2,
		('8.S9',2,11):   2,
		('8.S10',2,11):   2,
		('9.S12',2,11):   2,
		('8.S81t',2,11):   2,
		('8.S14',2,11):   2,
		('1.R12',2,11):   2,
		('2.R16',2,11):   2,
		('2.R15',2,11):   2,
		('9.RE3',2,11):   2,
		('9.RE2',2,11):   2,
		('9.S2',2,11):   2,
		('9.RE1a',2,11):   2,
		('9.RE4',2,11):   2,
		('9.R2',2,11):   2,
		('9.S1',2,11):   2,
		('9.RE1b',2,11):   2,
		('9.R3',2,11):   2,
		('9.R1',2,11):   2,
		('9.R4',2,11):   2,
		('1.R21',2,11):   2,
		('7.S4',2,11):   2,
		('7.S10',2,11):   2,
		('4.R1',2,11):   2,
		('7.S27',2,11):   2,
		('6.S31',2,11):   2,
		('6.S40',2,11):   2,
		('6.S13',2,11):   2,
		('6.S32',2,11):   2,
		('8.S4',2,11):   2,
		('8.S81s',2,11):   2,
		('4.RE3',2,11):   2,
		('4.RE2',2,11):   2,
		('4.R4',2,11):   2,
		('4.S4',2,11):   2,
		('4.S5',2,11):   2,
		('4.S44',2,11):   2,
		('4.S55',2,11):   2,
		('3.RE8',2,11):   2,
		('3.S7',2,11):   2,
		('3.S8',2,11):   2,
		('3.S9',2,11):   2,
		('1.R18',2,11):   2,
		('5.R1',2,11):   2,
		('6.S14b',2,11):   2,
		('6.S14a',2,11):   2,
		('2.R17',2,11):   2,
		('7.S24c',3,11):   2,
		('7.S9a',3,11):   2,
		('2.RE4a',3,11):   2,
		('2.RE4b',3,11):   2,
		('1.RE1',3,11):   2,
		('2.RE3',3,11):   2,
		('2.R14',3,11):   2,
		('2.R13',3,11):   2,
		('6.S10',3,11):   2,
		('6.RE2',3,11):   2,
		('6.S2',3,11):   2,
		('5.RE1',3,11):   2,
		('8.RE1',3,11):   2,
		('1.S2a',3,11):   2,
		('1.S2b',3,11):   2,
		('2.R8',3,11):   2,
		('2.R12',3,11):   2,
		('2.R10',3,11):   2,
		('2.R9',3,11):   2,
		('2.R11',3,11):   2,
		('4.R6',3,11):   2,
		('4.R5',3,11):   2,
		('6.S23a',3,11):   2,
		('6.S23b',3,11):   2,
		('6.S25',3,11):   2,
		('6.S26',3,11):   2,
		('6.S27',3,11):   2,
		('5.S28',3,11):   2,
		('6.S29',3,11):   2,
		('1.R3',3,11):   2,
		('1.R4',3,11):   2,
		('2.S9',3,11):   2,
		('2.S1',3,11):   2,
		('1.S3b',3,11):   2,
		('2.S4b',3,11):   2,
		('1.S3a',3,11):   2,
		('2.S4a',3,11):   2,
		('2.S5b',3,11):   2,
		('2.S5a',3,11):   2,
		('1.S7',3,11):   2,
		('2.S8',3,11):   2,
		('2.S40',3,11):   2,
		('2.S30',3,11):   2,
		('5.S1',3,11):   2,
		('5.S3c',3,11):   2,
		('5.S3b',3,11):   2,
		('5.S9',3,11):   2,
		('5.S3a',3,11):   2,
		('7.S24b',3,11):   2,
		('7.S8a',3,11):   2,
		('7.S5b',3,11):   2,
		('7.S2b',3,11):   2,
		('7.S2a',3,11):   2,
		('7.S3a',3,11):   2,
		('7.S3b',3,11):   2,
		('7.S5a',3,11):   2,
		('7.S6a',3,11):   2,
		('7.S6b',3,11):   2,
		('7.S7a',3,11):   2,
		('7.S7b',3,11):   2,
		('7.S8b',3,11):   2,
		('7.S8c',3,11):   2,
		('7.S9b',3,11):   2,
		('7.S12b',3,11):   2,
		('6.S42',3,11):   2,
		('7.S12a',3,11):   2,
		('7.S14b',3,11):   2,
		('7.S14a',3,11):   2,
		('7.S15a',3,11):   2,
		('7.S15b',3,11):   2,
		('7.S16b',3,11):   2,
		('7.S16a',3,11):   2,
		('7.S19a',3,11):   2,
		('7.S19b',3,11):   2,
		('7.S21',3,11):   2,
		('7.S24a',3,11):   2,
		('7.S25',3,11):   2,
		('6.S1',3,11):   2,
		('5.S18',3,11):   2,
		('6.S3',3,11):   2,
		('6.S9',3,11):   2,
		('5.S8',3,11):   2,
		('8.S6',3,11):   2,
		('6.S41',3,11):   2,
		('6.S30',3,11):   2,
		('6.S20',3,11):   2,
		('4.R7',3,11):   2,
		('1.R11',3,11):   2,
		('4.R3',3,11):   2,
		('2.R5',3,11):   2,
		('3.R11',3,11):   2,
		('8.S23',3,11):   2,
		('8.S22',3,11):   2,
		('8.S24',3,11):   2,
		('8.S21',3,11):   2,
		('8.S25',3,11):   2,
		('8.S26',3,11):   2,
		('1.R14',3,11):   2,
		('1.R15',3,11):   2,
		('1.R13',3,11):   2,
		('1.R6',3,11):   2,
		('2.S50',3,11):   2,
		('2.S60',3,11):   2,
		('1.R20',3,11):   2,
		('6.S16',3,11):   2,
		('3.RE1a',3,11):   2,
		('3.RE1b',3,11):   2,
		('3.RE2a',3,11):   2,
		('3.RE2b',3,11):   2,
		('3.RE4',3,11):   2,
		('4.RE1',3,11):   2,
		('3.R4b',3,11):   2,
		('3.R4a',3,11):   2,
		('3.R2',3,11):   2,
		('3.R1',3,11):   2,
		('3.R5',3,11):   2,
		('3.R6',3,11):   2,
		('3.R7',3,11):   2,
		('3.S1a',3,11):   2,
		('3.S2a',3,11):   2,
		('3.S44a',3,11):   2,
		('3.S44c',3,11):   2,
		('3.S1b',3,11):   2,
		('3.S2b',3,11):   2,
		('3.S3a',3,11):   2,
		('3.S3b',3,11):   2,
		('3.S4b',3,11):   2,
		('3.S4a',3,11):   2,
		('3.S5',3,11):   2,
		('3.S6',3,11):   2,
		('3.S51',3,11):   2,
		('3.S52',3,11):   2,
		('3.S31a',3,11):   2,
		('3.S31b',3,11):   2,
		('3.S44b',3,11):   2,
		('4.S6b',3,11):   2,
		('4.S7',3,11):   2,
		('4.S6a',3,11):   2,
		('4.S61',3,11):   2,
		('3.R8',3,11):   2,
		('3.R9',3,11):   2,
		('7.R2',3,11):   2,
		('2.R1',3,11):   2,
		('1.R16',3,11):   2,
		('1.R10',3,11):   2,
		('2.R4',3,11):   2,
		('2.R3',3,11):   2,
		('2.R2',3,11):   2,
		('2.R6',3,11):   2,
		('7.S18',3,11):   2,
		('6.S60',3,11):   2,
		('1.R19',3,11):   2,
		('1.R17',3,11):   2,
		('6.R1',3,11):   2,
		('8.S15',3,11):   2,
		('2.RE2',3,11):   2,
		('2.S20',3,11):   2,
		('2.S21',3,11):   2,
		('1.R5',3,11):   2,
		('4.R2',3,11):   2,
		('1.R22',3,11):   2,
		('1.R7',3,11):   2,
		('1.R9',3,11):   2,
		('1.R8',3,11):   2,
		('8.S30',3,11):   2,
		('8.S8b',3,11):   2,
		('8.S8c',3,11):   2,
		('8.S7',3,11):   2,
		('8.S35',3,11):   2,
		('7.S22',3,11):   2,
		('7.S29',3,11):   2,
		('7.S41a',3,11):   2,
		('7.S41b',3,11):   2,
		('7.S33',3,11):   2,
		('7.S26',3,11):   2,
		('8.S55',3,11):   2,
		('8.R1',3,11):   2,
		('8.S1',3,11):   2,
		('8.S2',3,11):   2,
		('8.S3',3,11):   2,
		('8.S5',3,11):   2,
		('8.S8a',3,11):   2,
		('8.S9',3,11):   2,
		('8.S10',3,11):   2,
		('9.S12',3,11):   2,
		('8.S81t',3,11):   2,
		('8.S14',3,11):   2,
		('1.R12',3,11):   2,
		('2.R16',3,11):   2,
		('2.R15',3,11):   2,
		('9.RE3',3,11):   2,
		('9.RE2',3,11):   2,
		('9.S2',3,11):   2,
		('9.RE1a',3,11):   2,
		('9.RE4',3,11):   2,
		('9.R2',3,11):   2,
		('9.S1',3,11):   2,
		('9.RE1b',3,11):   2,
		('9.R3',3,11):   2,
		('9.R1',3,11):   2,
		('9.R4',3,11):   2,
		('1.R21',3,11):   2,
		('7.S4',3,11):   2,
		('7.S10',3,11):   2,
		('4.R1',3,11):   2,
		('7.S27',3,11):   2,
		('6.S31',3,11):   2,
		('6.S40',3,11):   2,
		('6.S13',3,11):   2,
		('6.S32',3,11):   2,
		('8.S4',3,11):   2,
		('8.S81s',3,11):   2,
		('4.RE3',3,11):   2,
		('4.RE2',3,11):   2,
		('4.R4',3,11):   2,
		('4.S4',3,11):   2,
		('4.S5',3,11):   2,
		('4.S44',3,11):   2,
		('4.S55',3,11):   2,
		('3.RE8',3,11):   2,
		('3.S7',3,11):   2,
		('3.S8',3,11):   2,
		('3.S9',3,11):   2,
		('1.R18',3,11):   2,
		('5.R1',3,11):   2,
		('6.S14b',3,11):   2,
		('6.S14a',3,11):   2,
		('2.R17',3,11):   2,

	}

	# select a route in RouteInfoList1
	Route1 =  RouteInfoList1[-2]
	
	print "\nRouteInfo:"
	print PrettyStringRouteInfo(Route1)

	# Line Measurement Coverage of Route1 tells us, which LineKeys of LMRequirements
	# can be measured by the Measurement Variants of Route1.
	(LMCoverageOfRoutePerSegment, LMCoverageOfRoutePerLineKey) = \
		GetLMCoverageOfRoute(Route1, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)

	# PeriodBegin (first day of month), PeriodEnd (last day of month), 
	# ReqLineMeasureTime (required time in minutes for measuring a line)
	# are global parameters defined in BU2019_CentralParameters.py

	# display LM Coverage of Route per Segment & LineKey

	print "\nLMCoverageOfRoutePerSegment:"
	PrintDictionaryContent(LMCoverageOfRoutePerSegment)

	# Line Measurement (LM) Coverage of a Route: What a route can measure
	# (with all its varians) in terms of LineKeys (Line, TimeWindow, WeekdayGroup)

	print "\nLine Measurement (LM) Coverage of Route1 per LineKey"
	PrintDictionaryContent(LMCoverageOfRoutePerLineKey)

	# the LM Coverage of many routes can be added up
	# with the function AddDicValues() to obtain
	# the total LM coverage of many routes.

	# for example, let's see, which LineKeys of LMRequirements
	# can be covered by all routes of RouteInfoList1:
	LMCoverageTotal = {}
	for RouteInfo in RouteInfoList1:
		(LMCoveragePerSegment, LMCoveragePerLineKey) = \
			GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)
		
		LMCoverageTotal = AddDicValues(LMCoverageTotal, LMCoveragePerLineKey)

	print "\nLM Coverage of all routes in RouteInfoList1 (#LineKeys: %s)" % len(LMCoverageTotal)
	PrintDictionaryContent(LMCoverageTotal)

	totalReq=0
	totalCov=0

	for var in LMRequirementsAll:
		totalReq += LMRequirementsAll.get(var,"")


	for var in LMRequirementsAll:
		a=LMCoverageTotal.get(var,"")
		if LMCoverageTotal.get(var,"") == '':
			continue

		elif LMCoverageTotal.get(var,"") >= LMRequirementsAll.get(var,""):
			totalCov += LMRequirementsAll.get(var,"")
		
		else:
			totalCov += LMCoverageTotal.get(var,"")

	print "Coverage Percentage : %s" % (float(totalCov) / float(totalReq) * 100)

	# **************************************************************************************
	# Travel Segments
	# **************************************************************************************

	print LineSeparator 
	print "Travel Segments of a Route"
	print LineSeparator

	# Travel segments are defined by real change points:
	# A travel segment is a continuous trip without a line change.

	# get travel segments (Reisen) of Route1
	TravelSegments1 = GetTravelSegments(Route1, TimeWindows)

	print "\nTravelSegments1 (raw print dictionary)"
	PrintDictionaryContent(TravelSegments1)

	# TravelSegments1 is a dictionary whose values are lists with multiple field values.
	# The meaning and order of these fields are defined in global variable SegmentInfoInd
	# in BU2019_CentralParameters.py

	# For example, this is how you can get the LineID of segment 1:
	print "\nGet LineID of segment 1:"
	LineID_seg1 = TravelSegments1[1][SegmentInfoInd['line_id']]
	print "LineID_seg1 = %s" % LineID_seg1

	# Keys of the dictionary TravelSegments1 are simply ordered segment numbers (1, 2, ... N)

	# With the following function, travel segments can be displayed nicely 
	# together with the route information:

	print "\nDisplay TravelSegments1 nicely together with route information"
	print PrettyStringRouteSegmentsInfo(TravelSegments1)

	# **************************************************************************************
	# Route Segments
	# **************************************************************************************

	print LineSeparator 
	print "Route Segments of a Route"
	print LineSeparator

	# Unlike travel segments, route segments can have virtual change points 
	# for LineID and time window changes within the same continuous trip. 
	# Route segments are the basis for measurement variants of a route.
	RouteSegment1 =  GetRouteSegments(Route1, TimeWindows)

	print "\nRouteSegment1 (raw)"
	PrintDictionaryContent(RouteSegment1)

	# Route segments too can be displayed nicely together with the route information:

	print "\nDisplay RouteSegment1 nicely together with route information"
	print PrettyStringExtendedRouteSegmentsInfo(RouteSegment1)

	print Route1

	# Unless there are TimeWindow of LineID changes within continuous travels (Reisen, travel segments)
	# of a route, route segments are expected to be same as travel segments. 

	# Subsequent connections with the same FahrtID (trip_id) constitute a continuous 
	# travel segment (Reise)

	# Let's manipulate Route1 manually to display the difference of travel and route segments
	# by adding LineID and TimeWindow changes to the route:

	Route1_manipulated = [
	(8500000, 8507000, None, None, None, None, None, 'W', None, 8, 0, None, 8, 0, None, None, None), 
	(8507000, 8504489, 792580, '3.S5', 60995, 15528, 33, 'S', '5', 8, 8, 488, 8, 12, 492, '', 1), 
	(8504489, 8516154, 792581, '3.S5', 60995, 15528, 33, 'S', '5', 8, 12, 492, 8, 14, 494, '', 2), 

	# extend the duration of the trip to cause a TimeWindow change
	# within the same travel segment (notice same FahrtID 61373 of following connections)
	(8516154, 8504489, 795307, '3.S52', 61373, 16227, 33, 'S', '52', 8, 18, 498, 12, 0, 720, '', 5), 
	(8504489, 8507000, 795308, '3.S52', 61373, 16227, 33, 'S', '52', 12, 5, 725, 14, 26, 906, '', 6), 
	(8507000, 8503000, 48462, None, 4581, 709, 11, 'IC', '1', 14, 30, 910, 14, 45, 935, '', 2)]

	# Now compare the travel and tour segments of the manipulated tour Route1_manipulated
	print "\nDisplay manipulated route Route1_manipulated"
	print PrettyStringRouteInfo(Route1_manipulated)

	TravelSegments1_man = GetTravelSegments(Route1_manipulated, TimeWindows)
	print "\nDisplay TravelSegments of Route1_manipulated nicely together with route information"
	print PrettyStringRouteSegmentsInfo(TravelSegments1_man)

	RouteSegment1_man =  GetRouteSegments(Route1_manipulated, TimeWindows)
	print "\nDisplay RouteSegments of Route1_manipulated nicely together with route information"
	print PrettyStringExtendedRouteSegmentsInfo(RouteSegment1_man)

	# Note that in the Route1_manipulated, we have additional route segments due to 
	# LineID and TimeWindow changes within the same travel segment.

	# **************************************************************************************
	# Valuation and Sorting of Routes
	# **************************************************************************************

	# Route Value depends primarily on:
	# 1) what a route can measure (with all its measurement variants), 
	# 		and what is the monetary revenue from these line & station measurements
	# 2) what is the duration cost of a route

	print LineSeparator 
	print "Valuation and Sorting of Routes"
	print LineSeparator

	# There can be multiple valuation functions for routes. One of them is PlanEinsatz.GetSimpleLMRouteValue()

	N = 10
	print "\nGet the value of first %s routes in RouteInfoList1 (Valuation Func = GetSimpleLMRouteValue)" % N 

	RouteCounter = 0
	for RouteInfo in RouteInfoList1:
		RouteCounter += 1 
		
		RouteValue = GetSimpleLMRouteValue(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirementsAll, 
			RevenueLineMeasure, TripCostPerTimeInterval)
		print "Value of Route-%s: %s" % (RouteCounter, RouteValue)
		
		if RouteCounter == N:
			break

	# Sort Tours:
	# sort all the routes in RouteInfoList1 after their values, in descending order

	# select valuation function for sorting
	RouteValueFunc = GetSimpleLMRouteValue

	# Parameters is a tuple containing all input variables required for the valuation function
	ValueFuncParameters = (ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirementsAll, 
		RevenueLineMeasure, TripCostPerTimeInterval)

	# Note that you can pass any valuation function to the following sorting function.
	SortedRouteInfoList = SortRoutesAfterValueInDescOrder(RouteInfoList1, RouteValueFunc, ValueFuncParameters)

	N = 10
	print "\nGet the value of first %s routes in SortedRouteInfoList (Valuation Func = GetRouteValue)" % N 

	RouteCounter = 0
	for RouteInfo in SortedRouteInfoList:
		RouteCounter += 1 
		
		# alternative valuation function
		# RouteValue = GetRouteValue(RouteInfo, TimeWindows, ReqLineMeasureTime, StationMeasureTime_AQ, StationMeasureTime_KI, {}, 
		#	MinTimeIntvForStationMeasurements, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll, RailCountPerStation=None, LineToReqBundle=None)
		
		RouteValue = RouteValueFunc(RouteInfo, *ValueFuncParameters)

		print "\nValue of Route-%s: %s" % (RouteCounter, RouteValue)

		print PrettyStringRouteInfo(RouteInfo)
		
		if RouteCounter == N:
			break

	# **************************************************************************************
	# Availability of Routes
	# **************************************************************************************

	print LineSeparator 
	print "Availability of Routes (on week days)"
	print LineSeparator

	# get availability of Route1

	# StartDate: First day of month as date object 
	# EndDate: last day of month as date object
	# StartDate & EndDate are global variables defined in PlanInputParameters.py
	(AvailableDaysRoute, UnavailableDaysRoute) = GetAvailabilityOfRoute(Route1, StartDate, EndDate)

	# AvailableDaysRoute and UnavailableDaysRoute are lists of ordinal dates (day numbers)

	print "\nRoute1 is available on days (%s):" % len(AvailableDaysRoute)
	for DayOrd in AvailableDaysRoute:
		print "Date: %s - Weekday: %s" % (ConvertDateOrdinalToDateString(DayOrd), GetWeekdayOfDate(DayOrd))

	print "\nRoute1 is NOT available on days (%s):" % len(UnavailableDaysRoute)
	for DayOrd in UnavailableDaysRoute:
		print "Date: %s - Weekday: %s" % (ConvertDateOrdinalToDateString(DayOrd), GetWeekdayOfDate(DayOrd))

	