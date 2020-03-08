#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on: 12.02.2019 by Tunc Ali Kütükcüoglu
# https://software.tuncalik.com/
# Copyrights: Tunc Ali Kütükcüoglu (senior data analyst & developer)
"""
Central input parameters for graph algorithms and tour search with conditions.
(tour/path searching with conditions)
"""
import random
import sys 
from datetime import date 
from datetime import datetime
from datetime import timedelta
import calendar
import os

#######################################################################################
# Static Parameter Definitions
#######################################################################################

os.chdir('C:/Users/Grundig/Desktop/492/IE 492 Final Project/')

f = open('pass.txt', 'r')
pass_=f.readline()

# primary database
PrimaryDB = {
	'database': 'timetable2018_slim',
	'user': 'postgres',
	'port': '5432',
	'password':pass_,
}

# db tables
tbl_TimeTable = "timetable"

# Weekdays in text
WeekDays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

# elements of ConnectionInfo (ConnInfoInd[FieldName]=FieldIndex)
ConnInfoInd = {
	'station_from' : 		0, 		
	'station_to': 			1, 		
	'conn_id':				2,			# connection id
	'line_id': 				3,			# unique line id
	'travel_id':			4,
	'travel_no': 			5, 
	'management': 			6, 
	'line_category': 		7, 
	'line': 				8, 
	'departure_hour': 		9, 
	'departure_min': 		10,
	'departure_totalmin': 	11,
	'arrival_hour': 		12, 
	'arrival_min': 			13,
	'arrival_totalmin': 	14,
	'trafficdays_hexcode': 	15,
	'station_order':		16,
	}

# revenues & costs
RevenuePerLineMeasurement = 150.0
HourlyTravelCost = 60.0 			# 60 CHF per 60 minutes

# include/exclude options
INCLUDE_ALL_AND_ONLY = 1 		# includes all and only listed values
INCLUDE_ALL = 2 				# includes all listed values (any maybe more)
INCLUDE_ONLY = 3				# includes only (some of) listed values
EXCLUDE_ALL = 4 				# excludes all listed values

# total path duration, required for shortest path
TOTAL_PATH_DURATION = None

# platform: windows or linux (win)
MyPlatform = str(sys.platform)[0:3].lower()

# Weekday Groups (Wochentagtyp)
WD = {
	10: (1,2,3,4,5,6,7),
	11: (1,2,3,4,5),
	12: (6,),
	13: (7,),
}

# Zeitfenster (time windows)
ZF = {
	0: (0, 23*60 + 59),
	1: (0, 5*60 + 59),
	2: (6*60, 10*60 + 59),
	3: (11*60, 15*60 + 59),
	4: (16*60, 20*60 + 59),
	5: (21*60, 23*60 + 59)
}

#######################################################################################
# Helper Functions
#######################################################################################

def GetFirstAndLastDaysOfMonth_(year, month):
	"""
	Return first and last days of given month as date: date(year, month, day)
	"""
	# Get Last Day of the Month in Python
	# http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
	"""
	monthrange(year, month):
    Returns weekday of first day of the month and number of days in month
    """
	DayRange = calendar.monthrange(year,month)
	MonthEndDay = DayRange[1]
	StartDate = date(year,month,1)
	EndDate = date(year,month,MonthEndDay)		
	return (StartDate, EndDate)

def GetWeekdayGroupsOfDate_(WD, DateOrd, Exclude10 = True):
	"""
	Return WeekdayGroup(s) to which the weekday (1-7) of a given date ordinal date belongs.
	if Exclude10 = True, exclude 10 (all weekdays) from the output list.
	"""
	WeekDay = date.fromordinal(DateOrd).isoweekday()
	WeekdayGroups = set()
	for WDkey in WD:
		if WeekDay in WD[WDkey]:
			if not (WDkey == 10 and Exclude10):
				WeekdayGroups.add(WDkey)
	WeekdayGroups = list(WeekdayGroups)
	WeekdayGroups.sort()
	return WeekdayGroups

#######################################################################################
# General Input Parameters
#######################################################################################

# plan year begin/end (reference for Verkehrstage)
# see qdababav.fahrplan.eckdaten: start/ende
FPLAN_BeginDate = date(2017,12,10)
FPLAN_EndDate = date(2018,12,8)

# measurement period (first and last days of measurement period)
PlanYear = 2018
PlanMonth = 4

# plan months; relevant for both sample distribution and assignment planning
PlanMonths = range(1,11)

# start and end dates of month
(StartDate, EndDate) =  GetFirstAndLastDaysOfMonth_(PlanYear, PlanMonth)
PeriodBegin = StartDate 
PeriodEnd = EndDate

# DayList = [736062, 736063, 736064, ...]
DayList = range(StartDate.toordinal(), EndDate.toordinal()+1)
D = len(DayList)

# Way Attribbutes (ZuFuss Gattungen, für Haltestellenübergänge) - see METABHF (hafas text file)
TrWay = {}
TrWay['Y'] = 'ZF'		# Zu Fuss
TrWay['YM'] = 'ZF+M'	# Zu Fuss + Metro
TrWay['YB'] = 'ZF+B'	# Zu Fuss + Bus
TrWay['YT'] = 'ZF+T'	# Zu Fuss + Tram

