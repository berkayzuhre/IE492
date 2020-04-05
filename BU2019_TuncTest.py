#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Tunc Ali Kütükcüoglu (in 2019)
# see: https://software.tuncalik.com/travel-and-assignment-planning-software-in-python/4812
# Copyrights: Tunc Ali Kütükcüoglu (senior data analyst & developer)
"""
Test functions for TourSearch
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

# **************************************************************************************
# start
# **************************************************************************************

# database connection
dbcon = psycopg2.connect(**PrimaryDB) 
dbcur = dbcon.cursor()

def TEST_ReadTimeTable():

	# conditions for tour search
	RouteConditions1 = {
		# von und bis Haltestelle (mandatory condition)
		Cond.StartAndEndStations: (8507000, 8507000), 	
		
		# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
		# determines earliest and latest arrival to end station
		Cond.StartTimeAndDuration: (8, 0, 60, 90),		
		
		# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
		Cond.MaxWaitingTimeAtStation: (30,),			
		
		# Min nötige Umsteige-Zeit in Minuten (mandatory condition)
		Cond.TimeForLineChange: (2,),

		# Cond.ConnectionsAreAvailableOnAllListedDays: (['4-4-2016','5-4-2016','6-4-2016','7-4-2016','8-4-2016'],),
		Cond.ConnectionsAreAvailableOnAllListedDays: (GetWeekdaysOfMonth(PlanMonth, PlanYear, WD[11]),),
		}

	(TimeTableList, TimeTableIndex, StationHourIndex) = ReadTimeTable(dbcur, RouteConditions1)
	print "TimeTableList:"
	for line in TimeTableList:
		print line

def TEST_FindAndDisplayRoutes():
	RelevantLineCategories = ['IC','ICE','S']		# ['RE','R','S','IC','ICE']
	RelevantManagements = [11,33]

	# stations:
	# 8507000: Bern
	# 8503000: Zürich

	# conditions for tour search
	# Bern --> 8503000
	RouteConditions1 = {
		# von und bis Haltestelle (mandatory condition)
		Cond.StartAndEndStations: (8507000, 8503000), 	
		
		# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
		# determines earliest and latest arrival to end station
		Cond.StartTimeAndDuration: (8, 0, 100, 120),		
		
		# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
		Cond.MaxWaitingTimeAtStation: (30,),			
		
		# Min nötige Umsteige-Zeit in Minuten (mandatory condition)
		Cond.TimeForLineChange: (2,),

		Cond.IncludeListedGattungsOnly: (RelevantLineCategories,), 	
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

	print "\nFind all routes for the given route conditions..."
	(RouteInfoList, StatusReport, TerminationReasons) = FindAllRoutes(dbcur, RouteConditions1)

	print 
	print "StatusReport: " + str(StatusReport)
	print "TerminationReasons: " + str(TerminationReasons)
	print "length of RouteInfoList: %s" % len(RouteInfoList)

	N = 10

	print "\nDisplay first %s routes in RouteInfoList" % N
	ctr = 0
	for RouteInfo in RouteInfoList:
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
	TEST_FindAndDisplayRoutes() 