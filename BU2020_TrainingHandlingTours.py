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
	Cond.StartTimeAndDuration: (8, 0, 50, 100),		
	
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
	Cond.MaxSearchTimeInSeconds: (30,),
	}

RelevantLineCategories = ['S']		# ['RE','R','IR','IC','ICE','S']

# conditions for tour search
# Bern --> Bern
RouteConditions2 = {
	# von und bis Haltestelle (mandatory condition)
	Cond.StartAndEndStations: (8503000, 8503000), 	
	
	# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
	# determines earliest and latest arrival to end station
	Cond.StartTimeAndDuration: (8, 0, 50, 60),		
	
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
	RouteConditions = RouteConditions2

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
		('7.S3a', 2, 11): 	2,
		('7.S3a', 2, 12): 	2,
		('7.S3a', 2, 13):	2,

		('7.S6b', 3, 11): 	2,
		('7.S6b', 3, 12): 	2,
		('7.S6b', 3, 13):	2,

		('7.S24b', 2, 11): 	2,
		('7.S24b', 2, 12): 	2,
		('7.S24b', 2, 13):	2,

		('3.S52', 3, 11): 	2,
		('3.S52', 3, 12): 	2,
		('3.S52', 3, 13):	2,

		('3.S6', 2, 11): 	2,
		('3.S6', 2, 12): 	2,
		('3.S6', 2, 13):	2,
		('3.S6', 3, 11): 	2,
		('3.S6', 3, 12): 	2,
		('3.S6', 3, 13):	2,
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


	print  float(totalCov) / float(totalReq) * 100

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

	