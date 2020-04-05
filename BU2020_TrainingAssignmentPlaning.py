#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Tunc Ali Kütükcüoglu (on 28. Feb 2020)
# see: https://software.tuncalik.com/travel-and-assignment-planning-software-in-python/4812
# Copyrights: Tunc Ali Kütükcüoglu (senior data analyst & developer)
"""
Training script to explain the steps of Assignment Planning
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
from random import shuffle

from BU2019_CentralParameters import *
from BU2019_BasicFunctionsLib import *
from BU2019_TourSearch import *
from BU2020_AssignmentFunctions import *

# **************************************************************************************
# connection to local database
# **************************************************************************************

# connection to local db
dbcon = psycopg2.connect(**PrimaryDB) 
dbcur = dbcon.cursor()

# line separator string
LineSeparator = 100 * '*' 

# **************************************************************************************
# help functions
# **************************************************************************************

def GenerateTestData():
	"""
	Generate test data for assignment planning 
	RouteInfoList = RouteInfoList1 + RouteInfoList2

	where
	RouteInfoList1: Round tours Bern-->Bern (S-bahn only, from 8:00 to 8:50-9:00)
	RouteInfoList2: Round tours Zürich -->Zürich (S-bahn only, from 8:00 to 8:50-9:00)


	"""
	# define route conditions
	RelevantLineCategories = ['S']		# ['RE','R','IR','IC','ICE','S']
	RelevantManagements = [11,33]

	# stations:
	# 8507000: Bern
	# 8503000: Zürich

	# conditions for tour search
	# Bern --> Bern
	RouteConditions1 = {
		# von und bis Haltestelle (mandatory condition)
		Cond.StartAndEndStations: (8507000, 8507000), 	
		
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

	# conditions for tour search
	# Zürich --> Zürich
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

	print "\nFind routes for the given route conditions RouteInfoList1..."
	(RouteInfoList1, StatusReport, TerminationReasons) = FindAllRoutes(dbcur, RouteConditions1)

	print "\nFind routes for the given route conditions RouteInfoList2..."
	(RouteInfoList2, StatusReport, TerminationReasons) = FindAllRoutes(dbcur, RouteConditions2)

	# shuffle lists
	shuffle(RouteInfoList1) 
	shuffle(RouteInfoList2)

	RouteInfoList = RouteInfoList1[0:30] + RouteInfoList2[0:30] 

	# save variable to file
	SaveVariableToFile(RouteInfoList, PlanYear, PlanMonth, 'RouteInfoList', directory=VariableDirectory)

	# get total LM Coverage of all routes in RouteInfoList
	# note: LMRequirements can be set to None
	TotalLMCoveragePerLineKey = GetLMCoverageOfMultipleRoutes(RouteInfoList, ReqLineMeasureTime, PeriodBegin, PeriodEnd, 
		LMRequirements=None)

	print "\nTotal Potential LM Coverage of all Routes in RouteInfoList, per LineKey:" 
	PrintDictionaryContent(TotalLMCoveragePerLineKey)

	# save variable to file
	LMRequirementsAll = TotalLMCoveragePerLineKey
	SaveVariableToFile(LMRequirementsAll, PlanYear, PlanMonth, 'LMRequirementsAll', directory=VariableDirectory)


# **************************************************************************************
# Input Parameters: Plan Month
# **************************************************************************************

print "PlanYear = %s" % PlanYear
print "PlanMonth = %s" % PlanMonth

# first and last days of PlanMonth
(PlanMonthFirstDay, PlanMonthLastDay) = GetFirstAndLastDaysOfMonth(PlanYear, PlanMonth)
PlanMonthFirstDayOrd = PlanMonthFirstDay.toordinal()
PlanMonthLastDayOrd = PlanMonthLastDay.toordinal()

print "\nDays of Plan Month %s and Year %s:" % (PlanMonth, PlanYear)
for DayOrd in range(PlanMonthFirstDayOrd, PlanMonthLastDayOrd+1):
	print "Date: %s, DayOrd: %s, Weekday: %s" % (ConvertDateOrdinalToDateString(DayOrd), DayOrd, GetWeekdayOfDate(DayOrd))

# **************************************************************************************
# Input Parameters: Remaining Line Measurement (LM) Requirements
# Relevant TUs & Gattungs
# **************************************************************************************

print 
print LineSeparator
print "Remaining Line Measurement Requirements for PlanMonth"
print LineSeparator

# LM Requirements per LineKey (LineID, TimeWindow, WeekdayGroup):
# (remaining measurement requirements for the rest of the year)
LMRequirementsAll = {
	('3.S5', 2, 11): 	2,
	('3.S5', 2, 12): 	2,
	('3.S5', 2, 13):	2,
	('3.S5', 3, 11): 	2,
	('3.S5', 3, 12): 	2,
	('3.S5', 3, 13):	2,

	('3.S52', 2, 11): 	2,
	('3.S52', 2, 12): 	2,
	('3.S52', 2, 13):	2,
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

print "\nLMRequirements:"
PrintDictionaryContent(LMRequirementsAll)

# Get list of all required line IDs
LineList = set()
for key in LMRequirementsAll.keys():
	line = key[0]
	LineList.add(line)
print "\nAll required LineIDs (%s):" % len(LineList)
print LineList

# Relevant TUs and Gattings are required as limiting & filtering
# parameters for RouteConditions
RelevantTUs = None
RelevantGattungs = None 

# For the sake of completeness & simplicity, all lines are mapped to a single LineBundle
LineToBundle = {}
LBname = 'LineBundle-1'
for LineID in LineList:
	LineToBundle[LineID] = LBname

# station measurement requirements
StationMeasurementRequirementsPerLB = {}
StationMeasurementRequirementsPerLB[LBname] = 30 

# **************************************************************************************
# Input Parameters: Customer Preferences
# **************************************************************************************

print 
print LineSeparator
print "Customer Preferences"
print LineSeparator

# List of Test Customers (test travelers)
# AllTestCustomers[t] = NameOfTC
AllTestCustomers = {
	1: 	"Murtaza",
	2: 	"Hatice",
	3: 	"Manfred",
	4: 	"Elif",
}

print "\nAllTestCustomers:"
PrintDictionaryContent(AllTestCustomers)

# Depots: start station per test customer
# StartingStationTC[t] = StationNr 	(Depot)
# 8507000: Bern 
# 8503000: Zürich
StartStationPerTestCustomer = {
	1: 8507000, 		# Murtaza --> Bern
	2: 8507000, 		# Hatice --> Bern
	3: 8503000, 		# Manfred --> Zürich
	4: 8503000,			# Elif --> Zürich
}

print "\nStartStationPerTestCustomer:"
PrintDictionaryContent(StartStationPerTestCustomer)

# Availability: Availability of Test Customers
# Availability[(t,d)] = [(m1,m2),(m3,m4), ...] (or None, i.e. not available for the whole day)
# no key/value pair for key (t,d) means no time limits for (t,d)
Availability = {
	(1, 736147): None, 								# Saturday
	(1, 736148): None, 								# Sunday
	(1, 736149): [(8*60, 14*60),(16*60, 22*60)],	# Monday
	(1, 736154): None, 		
	(1, 736155): None, 
	(1, 736156): [(8*60, 14*60),(16*60, 22*60)],
	(1, 736161): None, 
	(1, 736162): None, 
	(1, 736163): [(8*60, 14*60),(16*60, 22*60)],
	(1, 736161): None, 
	(1, 736162): None, 
	(1, 736163): [(8*60, 14*60),(16*60, 22*60)],
	(1, 736168): None, 								# Saturday
	(1, 736169): None, 
	(1, 736170): [(8*60, 14*60),(16*60, 22*60)],
	(1, 736175): None, 
	(1, 736176): None, 
}

print "\nAvailability:"
PrintDictionaryContent(Availability)

# Minimum total number of trips per test customer in a month
# MinTripCountPerTC[t] = MinDayCount
MinTripCountPerTC = {
	1: 3, 
	2: 4, 
	3: 4, 
	4: 3,
}

print "\nMinTripCountPerTC:"
PrintDictionaryContent(MinTripCountPerTC)

# max number of subsequent days with assigned trips
MaxBlockDaysPerTC = {
	1: 2, 
	2: 3, 
	3: 1, 
	4: 3,
}

print "\nMinTripCountPerTC:"
PrintDictionaryContent(MinTripCountPerTC)

# **************************************************************************************
# Get selected tours from Travel Planning 
# **************************************************************************************

print 
print LineSeparator
print "Read selected routes from saved variable"
print LineSeparator

Read_TestData_FromFile = True
if not Read_TestData_FromFile: GenerateTestData()

RouteInfoList = ReadVariableFromFile(PlanYear, PlanMonth, 'RouteInfoList', directory=VariableDirectory)
if not RouteInfoList:
	raise Exception("RouteInfoList is Empty or None; no saved variable for routes!")

LMRequirementsAll = ReadVariableFromFile(PlanYear, PlanMonth, 'LMRequirementsAll', directory=VariableDirectory)
if not RouteInfoList:
	raise Exception("LMRequirementsAll is Empty or None; no saved variable for routes!")

print "There are %s routes in RouteInfoList" % len(RouteInfoList)


# given day of year, see BU2019_BasicFunctions.py for date functions
day = date(2018, 4, 10)
dayOrd = day.toordinal()

DateStr = ConvertDateToDateString(day)
Weekday = GetWeekdayOfDate(dayOrd)						# 1 for Monday, 7 for Sunday
WeekdayGroups = GetWeekdayGroupsOfDate(WD, dayOrd)  	# 11, 12, 13, 11 for workdays (Mon-Fri)
WeekdayGroup = WeekdayGroups[0]

print "\nGiven date: %s, Weekday: %s, WeekdayGroup: %s" % (DateStr, Weekday, WeekdayGroup)

# **************************************************************************************
# Routes, Travel Segments, LM Coverage
# **************************************************************************************

N = 10

print 
print LineSeparator
print "Display first %s routes in RouteInfoList with Travel Segments" % N
print LineSeparator

ctr = 0
for RouteInfo in RouteInfoList:
	ctr += 1 
	if ctr > N: break
	
	print "\n******* Route-%s ****************" % ctr

	# print raw RouteInfo
	print "\nRaw RouteInfo:"
	for conn in RouteInfo:
		conn = list(conn)
		conn[ConnInfoInd['trafficdays_hexcode']] = '-'
		print tuple(conn)

	print "\nRouteInfo:"
	print PrettyStringRouteInfo(RouteInfo)

	print "\nTravel Segment of RouteInfo:"
	TravelSegments = GetTravelSegments(RouteInfo, TimeWindows)
	print PrettyStringRouteSegmentsInfo(TravelSegments)

	# how to obtain LineID of a segment 
	print "\nGet LineID of segment 1:"
	LineID_seg1 = TravelSegments[1][SegmentInfoInd['line_id']]
	print "LineID_seg1 = %s" % LineID_seg1

	# get potential Line Measurement (LM) coverage of route (LMRequirements can be set to None)
	(LMCoveragePerSegment, LMCoveragePerLineKey) = \
		GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)

	print "\nPotential LM Coverage of Route per LineKey:" 
	PrintDictionaryContent(LMCoveragePerLineKey)

	# get concrete LM coverage of route for the given day
	print "\nConcrete LM Coverage of Route per LineKey for given date %s (WeekdayGroup=%s)" % (DateStr, WeekdayGroup)
	GetLMCoveragePerLineKeyForDay = GetLMCoverageOfRouteForGivenDay(RouteInfo, dayOrd, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)
	PrintDictionaryContent(GetLMCoveragePerLineKeyForDay)

# **************************************************************************************
# Total potential Line Measurement (LM) Coverage of all routes in RouteInfoList
# **************************************************************************************

print 
print LineSeparator
print "Get Total potential Line Measurement (LM) Coverage of all routes in RouteInfoList"
print LineSeparator

# note: LMRequirements can be set to None
TotalLMCoveragePerLineKey = GetLMCoverageOfMultipleRoutes(RouteInfoList, ReqLineMeasureTime, PeriodBegin, PeriodEnd, 
	LMRequirements=LMRequirementsAll)

print "\nTotal Potential LM Coverage of all Routes in RouteInfoList, per LineKey:" 
PrintDictionaryContent(TotalLMCoveragePerLineKey)


# **************************************************************************************
# Prepare Assignment Parameters
# **************************************************************************************

print 
print LineSeparator
print "Generate all parameters required for Assignment Planning"
print LineSeparator

AssignmentParameters = GenerateAssignmentPlanningVariables(RouteInfoList, StartStationPerTestCustomer, ReqLineMeasureTime, 
	PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)

print "\nAssignmentPlanParameters:\n" 
PrintDictionaryContent(AssignmentParameters)

# add other required parameters 
AssignmentParameters['StartStationPerTestCustomer'] = StartStationPerTestCustomer
AssignmentParameters['LMRequirements'] = LMRequirementsAll
AssignmentParameters['RevenueLineMeasure'] = RevenueLineMeasure
AssignmentParameters['CostLineMeasure'] = CostLineMeasure
AssignmentParameters['TripCostPerTimeInterval'] = TripCostPerTimeInterval
AssignmentParameters['RouteInfoList'] = RouteInfoList
AssignmentParameters['MinTripCountPerTC'] = MinTripCountPerTC

# UpperLimitLMperLineKey
MaxSurpLusLM = 2
UpperLimitLMperLineKey = {}
for LineKey in LMRequirementsAll:
	UpperLimitLMperLineKey[LineKey] = LMRequirementsAll[LineKey] + MaxSurpLusLM

AssignmentParameters['UpperLimitLMperLineKey'] = UpperLimitLMperLineKey

# **************************************************************************************
# Execute Assignment Planning
# **************************************************************************************

# set all assignment conditions

AssignmentConditions = {
	# mandatory condition
	AssignCond.FirstAndLastDaysOfMeasurementPeriod: (StartDate.toordinal(), EndDate.toordinal()),

	# only single TravelID per day is allowed
	AssignCond.SingleFahrtIDMeasurementPerDay: (True,),

	# minimum number of trips per Test Customer
	AssignCond.MinNumberOfTripsPerTC: 	(MinTripCountPerTC,),

	# upper limit to line measurements per LineKey
	AssignCond.MaxNumberOfMeasurementsPerLineKey:	(UpperLimitLMperLineKey,),

}

# find optimal solutions, simple optimization without foresight
(AssignmentSolution, SolutionValue, LMCoverageOfSolution, IncrementalValuePerTDR) = FindOptimalAssignmentSolution(AssignmentConditions, AssignmentParameters)

# save solution to file
SaveVariableToFile(AssignmentSolution, PlanYear, PlanMonth, 'AssignmentSolution', directory=VariableDirectory)

print "\nAssignment Solution (t,d,r):"
print PrettyStringAssignmentSolution(AssignmentSolution, AllTestCustomers)

print "\nLMCoverageOfSolution:" 
PrintDictionaryContent(LMCoverageOfSolution)

print "\nSolutionValue = %s" % SolutionValue

print "\nIncrementalValuePerTDR = %s" % IncrementalValuePerTDR