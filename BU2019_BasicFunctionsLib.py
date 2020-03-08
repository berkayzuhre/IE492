#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Tunc Ali Kütükcüoglu (2019)
# see: https://software.tuncalik.com/travel-and-assignment-planning-software-in-python/4812
"""
Module with elementary (general-purpose) functions used in tour and assignment planning.
""" 
# import psycopg2
import sys, os
import time
import math
from timeit import default_timer as timer
# import pandas as pd
# import pandas.io.sql as psql
import numpy as np
from datetime import date 
from datetime import datetime
from datetime import timedelta
import calendar
import random, math 

# save & restore variables
# http://stackoverflow.com/questions/6568007/how-do-i-save-and-restore-multiple-variables-in-python
import pickle

# get global parameters
from BU2019_CentralParameters import *

# **************************************************************************************
# Time and Date Functions
# **************************************************************************************
def ConvertMinuteToHourMinStr(TimeMin):
	"""
	Convert time in minutes to Hour:Minute string, like 200 --> '3:20'
	"""
	# http://stackoverflow.com/questions/22617/format-numbers-to-strings-in-python
	time_hour = int(math.ceil(TimeMin/60))
	time_min = int(math.ceil(TimeMin % 60))
	return "%02d:%02d" % (time_hour,time_min)

def ConvertMinuteToHourAndMin(TimeMin):
	"""
	Convert time in minutes to (Hour,Minute) pair
	"""
	# http://stackoverflow.com/questions/22617/format-numbers-to-strings-in-python
	time_hour = int(math.ceil(TimeMin/60))
	time_min = int(math.ceil(TimeMin % 60))
	return (time_hour,time_min)

def PrettyStringTime(hour, minute):
	"""
	Return a well-formatted time string like " 9:30"
	"""
	return "%02d:%02d" % (hour, minute)

def PrettyStringTimeMin(TimeMin):
	"""
	Convert time in total minutes (like 500 for 8:20) to 
	a well-formatted time string like " 8:20"

	Note: TimeMin can also be None, f.e. in a relative AggregatePath
	"""
	if TimeMin:
		return PrettyStringTime(*ConvertMinuteToHourAndMin(TimeMin))
	else:
		return str(TimeMin)

def ConvertDateOrdinalToDateString(DateOrd):
	"""
	Convert a date ordinal (date.toordinal()) to formatted date string
	"""
 	return date.fromordinal(DateOrd).strftime("%d-%m-%Y")

def ConvertDateToDateString(MyDate):
	"""
	Convert a date (date(2012,11,5)) to formatted date string
	"""
	return MyDate.strftime("%d-%m-%Y")

def ConvertDateToOrdinal(MyDate):
	"""
	Convert a date (date(2012,11,5)) to ordinal date number
	"""
	return MyDate.toordinal()

def ConvertOrdinalToDate(DateOrd):
	"""
	Convert ordinal date to date variable like date(210,11,22)
	"""
	return date.fromordinal(DateOrd)

def GetFirstAndLastDaysOfMonth(year, month):
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

def GetWeekdayOfDate(DateOrd):
	"""
	Return weekday (1-7) of ordinal date.
	1 is for Monday, 7 is for Sunday.
	"""
	return (date.fromordinal(DateOrd)).isoweekday()

def GetWeekdayGroupsOfDate(WD, DateOrd, Exclude10 = True):
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

def GetMatchingTimeWindows(ZF, IntervalStart, IntervalEnd, MeasureTime):
	"""
	Return matching time windows (Zeitfenster) as a list, like [2,3].
	Returns empty list [] if no time window can be matched to given time interval.

	Matching Time Windows means: In which time windows could a measurement be done,
	within the given time interval.

	IntervalStart: Start of interval in minutes, like 8*60 
	IntervalEnd: End of interval in minutes, like 17*60+30
	MeasureTime: Required (minimum) measurement time in minutes

	NOTE:
	How many minutes can a measurement continue into following time window?
	RequiredMeasureTime -1? Is it decisive at which line the measurement has started?
	"""
	MatchingTimeWindows =   []
	for key in ZF:
		TimeWindow = ZF[key]
		TimeWindowBegin = TimeWindow[0]
		TimeWindowEnd = TimeWindow[1] + (MeasureTime - 1) 	# check assumption !!!

		OverlapTime = GetIntersectionLengthOfTwoLines(IntervalStart, IntervalEnd, TimeWindowBegin, TimeWindowEnd)
		if OverlapTime >= MeasureTime:
			MatchingTimeWindows.append(key)
	return MatchingTimeWindows

def FindTimeWindowOfTimePoint(ZF, TimePoint):
	"""
	Return time window index of the given time point in minutes. 
	Don't include time window index 0; return an TW value >= 1.

	Return MatchingTimeWindow
	Function added at: 16.09.2016 
	"""
	MatchingTimeWindow = None
	DMin = 24*60 
	
	for key in ZF:
		if key == 0: continue 
		(TimeWindowBegin, TimeWindowEnd) = ZF[key]
		if (TimePoint >= TimeWindowBegin and TimePoint <= TimeWindowEnd) or (TimePoint >= TimeWindowBegin+DMin and TimePoint <= TimeWindowEnd+DMin):
			MatchingTimeWindow = key
			break 
	return MatchingTimeWindow

def GetTimeWindowSpanOfTimePoints(ZF, TimePointList):
	"""
	Return list of TimeWindows like [2,3,4] spanned by given list 
	of time points (departure times, abfahrtm).
	"""
	TimeWindows = set()
	for tp in TimePointList:
		tw = FindTimeWindowOfTimePoint(ZF, tp)
		if tw: TimeWindows.add(tw)
	return list(TimeWindows)

def GetMeasurableTimeWindowSpan(ZF, TimePointList, MinMeasureTime):
	"""
	Return list of measurable TimeWindows like [2,3,4] spanned by given list 
	of ordered time points (departure times, abfahrtm).
	
	MinMeasureTime: Minimum measurement time in minutes
	"""
	TimeWindows = set()
	LastTimePoint = TimePointList[-1]
	for tp in TimePointList[0:-1]:
		if LastTimePoint - tp >= MinMeasureTime:
			tw = FindTimeWindowOfTimePoint(ZF, tp)
			if tw: TimeWindows.add(tw)
	return list(TimeWindows)

def GetWeekdaysOfMonth(month, year, WeekdayList, DecemberOption=0):
	"""
	Return a list of ordinal dates of month that correspond to 
	given weekdays in WeekdayList (like [1,5,7], where 1 is Monday).

	DecemberOption:
	0: from 1. to last day of month, including December 
	1: from 1. Dec to FPLAN_EndDate (this year)
	2: from FPLAN_BeginDate to 31. Dec (previous year) + from 1. Dec to FPLAN_EndDate (this year)
	"""
	(FirstDay, LastDay) = GetFirstAndLastDaysOfMonth(year, month)
	FirstDayOrd = ConvertDateToOrdinal(FirstDay)
	LastDayOrd = ConvertDateToOrdinal(LastDay)

	MatchingDayList = []
	DateRange = []

	if month < 12 or DecemberOption == 0:
		DateRange = range(FirstDayOrd, LastDayOrd+1)
	else:
		if DecemberOption == 1:
			# from 1. Dec to FPLAN_EndDate (this year)
			DateRange = range(FirstDayOrd, FPLAN_EndDate.toordinal()+1)
		
		elif DecemberOption == 2:
			# from FPLAN_BeginDate to 31. Dec (previous year) + from 1. Dec to FPLAN_EndDate (this year)
			DateRange = range(FPLAN_BeginDate.toordinal(), date(PlanYear-1,12,31).toordinal() + 1) + \
				range(FirstDayOrd, FPLAN_EndDate.toordinal()+1)
		else:
			raise Exception("Undefined DecemberOption %s!" % DecemberOption)

	for d in DateRange:
		if GetWeekdayOfDate(d) in WeekdayList:
			MatchingDayList.append(d)
	
	return MatchingDayList 

def GetWeekdaysOfMonthString(month, year, WeekdayList, DecemberOption=0):
	"""
	Return a list of string dates of month that correspond to 
	given weekdays in WeekdayList (like [1,5,7], where 1 is Monday).

	DecemberOption:
	0: from 1. to last day of month, including December 
	1: from 1. Dec to FPLAN_EndDate (this year)
	2: from FPLAN_BeginDate to 31. Dec (previous year) + from 1. Dec to FPLAN_EndDate (this year)
	"""
	(FirstDay, LastDay) = GetFirstAndLastDaysOfMonth(year, month)
	FirstDayOrd = ConvertDateToOrdinal(FirstDay)
	LastDayOrd = ConvertDateToOrdinal(LastDay)

	MatchingDayList = []
	DateRange = []

	if month < 12 or DecemberOption == 0:
		DateRange = range(FirstDayOrd, LastDayOrd+1)
	else:
		if DecemberOption == 1:
			# from 1. Dec to FPLAN_EndDate (this year)
			DateRange = range(FirstDayOrd, FPLAN_EndDate.toordinal()+1)
		
		elif DecemberOption == 2:
			# from FPLAN_BeginDate to 31. Dec (previous year) + from 1. Dec to FPLAN_EndDate (this year)
			DateRange = range(FPLAN_BeginDate.toordinal(), date(PlanYear-1,12,31).toordinal() + 1) + \
				range(FirstDayOrd, FPLAN_EndDate.toordinal()+1)
		else:
			raise Exception("Undefined DecemberOption %s!" % DecemberOption)

	for d in DateRange:
		if GetWeekdayOfDate(d) in WeekdayList:
			MatchingDayList.append(ConvertDateOrdinalToDateString(d))

	return MatchingDayList 

def ConvertDayOrdListToDayStrList(DayOrdList):
	"""
	Covert a list of ordinal dates to a list of string dates like ['12-8-2016', '14-8-2016']
	"""
	DayStrList = []
	for d in DayOrdList:
		DayStrList.append(ConvertDateOrdinalToDateString(d))
	return DayStrList

def GetWeekdaysOfPeriod(FirstDayOrd, LastDayOrd, WeekdayList):
	"""
	Return a list of ordinal dates of period that correspond to 
	given weekdays in WeekdayList (like [1,5,7], where 1 is Monday).
	"""
	MatchingDayList = []
	for d in range(FirstDayOrd, LastDayOrd+1):
		if GetWeekdayOfDate(d) in WeekdayList:
			MatchingDayList.append(d)
	return MatchingDayList

def GetDayMonthYearOfDate(DateOrd):
	"""
	Return (day,month,year)
	"""
	d = date.fromordinal(DateOrd)
	return (d.day, d.month, d.year)


def GetAvailabilityPerWeekdayInPeriod(DayOrdList, FirstDayOfPeriod, LastDayOfPeriod, WeekdayGroups=WD):
	"""
	Return a list of weekdays on those the month day is always available (i.e. in DayOrdList),
	within the given period (FirstDayOfPeriod, LastDayOfPeriod).

	DayOrdList: List of ordinal dates for availability 
	FirstDayOfPeriod: First day of period (as date)
	LastDayOfPeriod: Last day of period (as date)

	Weekday from 1 to 7, where 1 is Monday (datetime.date.isoweekday())

	Return: (AlwaysAvailableWeekdays, FullyAvailableWeekdayGroups, AvailableDaysPerWeekday)

	Func created on 15.12.2017 by Tunc 
	"""
	FirstDayOfPeriod_ord = FirstDayOfPeriod.toordinal()
	LastDayOfPeriod_ord = LastDayOfPeriod.toordinal()

	if LastDayOfPeriod_ord <= FirstDayOfPeriod_ord:
		raise Exception("LastDayOfPeriod_ord must be larger than FirstDayOfPeriod_ord!")
	
	AlwaysAvailableWeekdays = range(1,8)
	FullyAvailableWeekdayGroups = WD.keys()
	FullyAvailableWeekdayGroups.remove(10)
	
	AvailableDaysPerWeekday = {}
	for i in range(1,8):
		AvailableDaysPerWeekday[i] = []
	
	for d in range(FirstDayOfPeriod_ord, LastDayOfPeriod_ord):
		weekday = date.fromordinal(d).isoweekday()
		wdgroup = GetWeekdayGroupsOfDate(WeekdayGroups, d)[0]
		if d not in DayOrdList:
			if weekday in AlwaysAvailableWeekdays:
				AlwaysAvailableWeekdays.remove(weekday)
			if wdgroup in FullyAvailableWeekdayGroups:
				FullyAvailableWeekdayGroups.remove(wdgroup)
		else:
			AvailableDaysPerWeekday[weekday].append(d)
	
	return (AlwaysAvailableWeekdays, FullyAvailableWeekdayGroups, AvailableDaysPerWeekday)

def GetAvailableDaysPerWeekdayGroup(AvailableDaysPerWeekday, WeekdayGroups=WD):
	"""
	Convert (aggregate) AvailableDaysPerWeekday to AvailableDaysPerWeekdayGroup.

	AvailableDaysPerWeekday[WeekdayNr] = [list of ordinal dates]

	WeekdayNr = 1 for Monday
	WeekdayNr = 7 for Sunday

	Return AvailableDaysPerWeekdayGroup like:
		AvailableDaysPerWeekdayGroup[11] = [d1, d2, ...]

	Created on 26.01.2018 by Tunc
	"""
	WeekdayGrp = WeekdayGroups.keys()
	WeekdayGrp.remove(10)

	# map from Weekday to WeekdayGroup
	WDayToWGroup = {}
	for wg in WeekdayGrp:
		for wd in WeekdayGroups[wg]:
			WDayToWGroup[wd] = wg

	AvailableDaysPerWeekdayGroup = {}
	for wg in WeekdayGrp:
		AvailableDaysPerWeekdayGroup[wg] = []

	for wd in AvailableDaysPerWeekday:
		wg = WDayToWGroup[wd]
		for d in AvailableDaysPerWeekday[wd]:
			AvailableDaysPerWeekdayGroup[wg].append(d)

	return AvailableDaysPerWeekdayGroup

def GetAvailableWeekdayGroups(DayOrdList, FirstDayOfPeriod, LastDayOfPeriod, WeekdayGroups=WD):
	"""
	Return fully covered and partially covered weekday goups in period.

	fully covered: All days of corresponding WeekdayGroup are available within the period.
	
	DayOrdList: List of available ordinal dates
	FirstDayOfPeriod: First day of period (as date)
	LastDayOfPeriod: Last day of period (as date)

	Return: (FullyCoveredWeekdayGroups, PartiallyCoveredWeekdayGroups)

	Function created by Tunc on 9. Feb 2018
	"""
	FirstDayOfPeriod_ord = FirstDayOfPeriod.toordinal()
	LastDayOfPeriod_ord = LastDayOfPeriod.toordinal()

	AllWeekdayGroups = WeekdayGroups.keys()
	AllWeekdayGroups.remove(10)

	FullyCoveredWeekdayGroups = list(AllWeekdayGroups)
	PartiallyCoveredWeekdayGroups = []

	for d in range(FirstDayOfPeriod_ord, LastDayOfPeriod_ord):
		wdgroup = GetWeekdayGroupsOfDate(WeekdayGroups, d)[0]
		
		if d not in DayOrdList:
			if wdgroup in FullyCoveredWeekdayGroups:
				FullyCoveredWeekdayGroups.remove(wdgroup)
		else:
			if not wdgroup in PartiallyCoveredWeekdayGroups:
				PartiallyCoveredWeekdayGroups.append(wdgroup)

	# clean PartiallyCoveredWeekdayGroups
	for wdgroup in FullyCoveredWeekdayGroups:
		if wdgroup in PartiallyCoveredWeekdayGroups:
			PartiallyCoveredWeekdayGroups.remove(wdgroup)

	return (FullyCoveredWeekdayGroups, PartiallyCoveredWeekdayGroups)

def GetCoveredWeekdayGroups(DayOrdList, WeekdayGroups=WD):
	"""
	Return the list of covered weekday groups like [11, 13]
	"""
	AllWeekdayGroups = WeekdayGroups.keys()
	AllWeekdayGroups.remove(10)
	AllWeekdayGroups = set(AllWeekdayGroups)

	CoveredWeekdayGroups = set() 

	for d in DayOrdList:
		wdgroup = GetWeekdayGroupsOfDate(WeekdayGroups, d)[0]
		CoveredWeekdayGroups.add(wdgroup)
		if CoveredWeekdayGroups == AllWeekdayGroups:
			return list(CoveredWeekdayGroups)

	return list(CoveredWeekdayGroups)

def GetAvailableWeekdayGroups_and_AvailableDaysPerWeekdayGroup(DayOrdList, FirstDayOfPeriod, LastDayOfPeriod, WeekdayGroups=WD):
	"""
	Return fully covered and partially covered weekday goups,
	and list of available days per WeekdayGroup in period.

	fully covered: All days of corresponding WeekdayGroup are available within the period.
	
	DayOrdList: List of available ordinal dates
	FirstDayOfPeriod: First day of period (as date)
	LastDayOfPeriod: Last day of period (as date)

	Return: (FullyCoveredWeekdayGroups, PartiallyCoveredWeekdayGroups, AvailableDaysPerWeekdayGroup)

	Function created by Tunc on 9. Feb 2018
	"""
	FirstDayOfPeriod_ord = FirstDayOfPeriod.toordinal()
	LastDayOfPeriod_ord = LastDayOfPeriod.toordinal()

	AllWeekdayGroups = WeekdayGroups.keys()
	AllWeekdayGroups.remove(10)

	FullyCoveredWeekdayGroups = list(AllWeekdayGroups)
	PartiallyCoveredWeekdayGroups = []

	AvailableDaysPerWeekdayGroup = {}
	for wg in AllWeekdayGroups:
		AvailableDaysPerWeekdayGroup[wg] = []

	for d in range(FirstDayOfPeriod_ord, LastDayOfPeriod_ord):
		wdgroup = GetWeekdayGroupsOfDate(WeekdayGroups, d)[0]
		
		if d not in DayOrdList:
			if wdgroup in FullyCoveredWeekdayGroups:
				FullyCoveredWeekdayGroups.remove(wdgroup)
		else:
			if not wdgroup in PartiallyCoveredWeekdayGroups:
				PartiallyCoveredWeekdayGroups.append(wdgroup)
			AvailableDaysPerWeekdayGroup[wdgroup].append(d)

	# clean PartiallyCoveredWeekdayGroups
	for wdgroup in FullyCoveredWeekdayGroups:
		if wdgroup in PartiallyCoveredWeekdayGroups:
			PartiallyCoveredWeekdayGroups.remove(wdgroup)

	return (FullyCoveredWeekdayGroups, PartiallyCoveredWeekdayGroups, AvailableDaysPerWeekdayGroup)

def ReportAvailabilityInPeriod(DayOrdList, FirstDayOfPeriod, LastDayOfPeriod, 
	WeekdayGroups=WD, WeekdayNames=WeekDays):
	"""
	Return a readable string showing availability information for the period.

	Possibilities:
	a) Available on every day (of period)
	b) Always available on weekdays ... and fully available for weekday groups ...
	c) Additionaly, available on Mondays ... on Tuesdays ...

	Short form:
	Always available on weekdays [...] + (additional dates)

	return (ShortStr, LongStr)
	"""
	LongStr = ""
	ShortStr = ""

	# get availability info
	(AlwaysAvailableWeekdays, FullyAvailableWeekdayGroups, AvailableDaysPerWeekday) = \
	 	GetAvailabilityPerWeekdayInPeriod(DayOrdList, FirstDayOfPeriod, LastDayOfPeriod, WeekdayGroups)

	if len(AlwaysAvailableWeekdays) == 7:
		LongStr = "Available on all weekdays"
		ShortStr = "Available on all weekdays"
		return (ShortStr, LongStr)

	if AlwaysAvailableWeekdays:
		LongStr = "Always available on Weekdays %s " % str(AlwaysAvailableWeekdays)
		ShortStr = "weekdays %s " % str(AlwaysAvailableWeekdays)

	if FullyAvailableWeekdayGroups:
		LongStr += "and WeekdayGroups %s " % str(FullyAvailableWeekdayGroups)
		ShortStr += "wdgroups %s " % str(FullyAvailableWeekdayGroups)

	# check if there are additional (exceptional) available weekdays not covered by AlwaysAvailableWeekdays
	IfExceptionalWeekdays = False 
	for wd in range(1,8):
		if not wd in AlwaysAvailableWeekdays and AvailableDaysPerWeekday[wd]:
			IfExceptionalWeekdays = True 
			break 

	if IfExceptionalWeekdays:
		LongStr += "\nAlso available on following weekday(s):"
		ShortStr += "+"
		for wd in AvailableDaysPerWeekday:
			if wd in AlwaysAvailableWeekdays or not AvailableDaysPerWeekday[wd]:
				continue 
			WeekdayName = '{:<11}'.format(str(WeekdayNames[wd-1]) + ":")
			AvailableDateList = ConvertDayOrdListToDayStrList(AvailableDaysPerWeekday[wd])
			AvailableDates = ", ".join(AvailableDateList)
			LongStr += "\n%s %s" % (WeekdayName, AvailableDates)

	return (ShortStr, LongStr)


# **************************************************************************************
# Dictionary Functions
# **************************************************************************************

def AddDicValues(dic1, dic2, DefaultEmptyVal = 0):
	"""
	Add scalar values of two dictionaries:
	dic3[key] = dic1[key] + dic2[key]

	dic3 contains all keys of dic1 and dic2 (union of keys).
	if a dictionary doesn't have a key, corresponding value is assumed DefaultEmptyVal
	"""
	UnionKeys = set(dic1.keys()).union(set(dic2.keys()))
	dic = {}
	for key in UnionKeys:
		v1 = None
		v2 = None
		if dic1.has_key(key):
			v1 = dic1[key]
		else:
			v1 = DefaultEmptyVal
		if dic2.has_key(key):
			v2 = dic2[key]
		else:
			v2 = DefaultEmptyVal
		dic[key] = v1 + v2 
	return dic

def SubtractDicValues(dic1, dic2, DefaultEmptyVal = 0):
	"""
	Subtract scalar values of two dictionaries:
	dic3[key] = dic1[key] - dic2[key]

	dic3 contains all keys of dic1 and dic2 (union of keys).
	if a dictionary doesn't have a key, corresponding value is assumed DefaultEmptyVal
	"""
	UnionKeys = set(dic1.keys()).union(set(dic2.keys()))
	dic = {}
	for key in UnionKeys:
		v1 = None
		v2 = None
		if dic1.has_key(key):
			v1 = dic1[key]
		else:
			v1 = DefaultEmptyVal
		if dic2.has_key(key):
			v2 = dic2[key]
		else:
			v2 = DefaultEmptyVal
		dic[key] = v1 - v2 
	return dic

def DeleteKeysFromDic(dic, KeyList):
	"""
	Delete given key-value pairs from dictionary
	"""
	dicr = {}
	for key in dic:
		if key not in KeyList:
			dicr[key] = dic[key]
	return dicr

def SelectKeysFromDic(dic, KeyList):
	"""
	Select given key-value pairs from dictionary
	"""
	dicr = {}
	for key in dic:
		if key in KeyList:
			dicr[key] = dic[key]
	return dicr

def CheckIfEqualOrLargerDic(dic1, dic2, DefaultEmptyVal = 0):
	"""
	Check if all values of dic1 are equal to or larger than corresponding values in dic2.
	If not, return False.

	A nonexisting value in dic2 is assumed DefaultEmptyVal
	"""
	for key in dic2:
		v1 = DefaultEmptyVal
		v2 = DefaultEmptyVal
		if dic1.has_key(key):
			v1 = dic1[key]
		if dic2.has_key(key):
			v2 = dic2[key]
		if v1 < v2: 
			return False
	return True

def CheckIfLargerDic(dic1, dic2, DefaultEmptyVal = 0):
	"""
	Check if all values of dic1 are larger than corresponding values in dic2.
	If not, return False.

	A nonexisting value in dic2 is assumed DefaultEmptyVal
	"""
	for key in dic2:
		v1 = DefaultEmptyVal
		v2 = DefaultEmptyVal
		if dic1.has_key(key):
			v1 = dic1[key]
		if dic2.has_key(key):
			v2 = dic2[key]
		if v1 <= v2: 
			return False
	return True

def CheckIfEqualDic(dic1, dic2, DefaultEmptyVal = 0):
	"""
	Check if all values of dic1 are equal to corresponding values in dic2.
	If not, return False.

	A nonexisting value in dic1 or dic2 is assumed DefaultEmptyVal
	"""
	UnionKeys = set(dic1.keys()).union(set(dic2.keys()))
	dic = {}
	for key in UnionKeys:
		v1 = None
		v2 = None
		if dic1.has_key(key):
			v1 = dic1[key]
		else:
			v1 = DefaultEmptyVal
		if dic2.has_key(key):
			v2 = dic2[key]
		else:
			v2 = DefaultEmptyVal
		if v1 != v2:
			return False
	return True

def IncrementDicValue(dic, key):
	"""
	dic[key] +=1
	"""
	if not dic.has_key(key): dic[key] = 0 
	dic[key] += 1 

def SelectDictionaryItemsWithKeyIndices(dic, KeyIndices, FixValue=None):
	"""
	Select dictionary items with given key indices, like [0,2,3,5]
	to return a filtered dictionary.
	"""
	FilteredDic = {}
	KeyList = dic.keys() 
	for key in KeyIndices:
		if FixValue:
			FilteredDic[KeyList[key]] = FixValue
		else:
			FilteredDic[KeyList[key]] = dic[KeyList[key]]
	return FilteredDic

def SelectDictionaryItemsWithKeys(dic, Keys, FixValue=None):
	"""
	Select dictionary items with given list of keys, like ['ali', 'veli', 'hasan']
	to return a filtered dictionary.
	"""
	FilteredDic = {}
	for key in Keys:
		if not dic.has_key(key): 
			continue
		if FixValue:
			FilteredDic[key] = FixValue
		else:
			FilteredDic[key] = dic[key]
	return FilteredDic

def CyclicElementSelectionFromDictionary(dic, SortKeys=False):
	"""
	Return a list filled with cyclic element selection from dictionary.
	Each dictionary value is a vector, from which the elements are selected.

	dic[k1] = [a1, a2, a3, a4]
	dic[k2] = [b1, b2]

	return: [a1, b1, a2, b2, a3, a4]
	"""
	KeyList = dic.keys()
	if SortKeys: KeyList.sort()
	KeyCount = len(KeyList)

	# vector size per key
	DicSize = {}
	for key in KeyList:
		DicSize[key] = len(dic[key])

	# index counter per key
	DicCounter = {}
	for key in KeyList:
		DicCounter[key] = 0 

	SelectedElements = [] 
	EndOfDic = False 
	ctr = 0 
	while not EndOfDic:
		ind = ctr % KeyCount
		key = KeyList[ind]
		if DicCounter[key] < DicSize[key]:
			SelectedElements.append(dic[key][DicCounter[key]])
			DicCounter[key] += 1 
		ctr += 1 

		EndReached = True
		for key in KeyList:
			if DicCounter[key] < DicSize[key]:
				EndReached = False
				break 
		EndOfDic = EndReached
	return SelectedElements

def PrintDictionaryContent(dic, SortKeys=True, N=None):
	"""
	Print dictionary content: "key: value" pair per line
	if N = None, display all key-value pairs, otherwise display only N value pairs
	"""
	if N: 
		print "-- display first %s key-value pairs --" % N
	else:
		# print "-- display all key-value pairs --"
		pass

	keys = dic.keys()
	if SortKeys: keys.sort()
	ctr = 0
	for key in keys:
		print str(key) + ": " + str(dic[key])
		ctr += 1 
		if N and ctr == N:
			break 

def CheckIfLineIDAndTimeWindowInKey(LMdic, LineID, TimeWindow):
	"""
	Return True if LineID, Window pair is included in any 
	key (LineID, TimeWindow, WG) of LMdic.
	"""
	if not LMdic:
		return False 
	for key in LMdic:
		if key[0] == LineID and key[1] == TimeWindow:
			return True 
	return False

def Convert_perLineKey_to_perLine(LMperLineKey):
	"""
	Convert LM[LineKey] to LM[LineID]
	"""
	LMperLine = {}
	for LineKey in LMperLineKey:
		(LineID, TW, WG) = LineKey 
		if not LineID in LMperLine:
			LMperLine[LineID] = 0 
		LMperLine[LineID] += LMperLineKey[LineKey]
	return LMperLine

def SelectRandomSubDictionaryWithPositiveIntegerValues(dic, N, divisor=1):
	"""
	Select a sub-dictionary with N randomly selected keys,
	with a corresponding random value from 1 to dic value.
	
	Dictionary must have positive integers as values, like LMRequirements.
	"""
	keys = dic.keys()
	random.shuffle(keys)
	subdic = {}
	for key in keys[0:N]:
		subdic[key] = random.randint(1, math.ceil(dic[key]/divisor))
	return subdic

def ConvertKeyFromLineKeyToLineTW():
	pass

def GetMinValueOfLineTW_from_LineKey(ValuesPerLineKey, LineID, TimeWindow, WGroups):
	"""
	Get minimum value of ValuesPerLineKey for given (LineID, TimeWindow)
	over given list of WeeekdayGroup values like [11, 12].

	Lowest min value = 0
	"""
	if not ValuesPerLineKey:
		return 0 
	if not WGroups:
		return 0 

	MinVal = 999
	for WG in WGroups:
		LineKey = (LineID, TimeWindow, WG)
		if not LineKey in ValuesPerLineKey:
			return 0 
		else:
			MinVal = min(MinVal, ValuesPerLineKey[LineKey])
	return MinVal

def GetDeltaForShiftingLMRequirements(LMCoveragePerLineKey, LowerLimitLMperLineKey, ZF=ZF, WD=WD):
	"""
	Generate delta dictionary for shifting values in LowerLimitLMperLineKey,
	so that shifted values in LowerLimitLMperLineKey are covered by LMCoveragePerLineKey.

	Covered meanys LineKey exists in LMCoveragePerLineKey AND LMCoveragePerLineKey[LineKey] > 0
	LineKey: (LineID, TimeWindowID, WeekdayTypeID)

	Shifting method:
	TimeWindows are shifted from 1 --> 2,3, .. or 5 --> 4,3, ..
	WeekdayTypes are shifted from 13 --> 12, 11

	Function created on 18.10.2017 in Beldibi/Antalya 
	"""
	ZFkeys = ZF.keys()[1:]
	WDkeys = WD.keys()[1:]
	DeltaDic = {}
	
	for lkey in LowerLimitLMperLineKey:
		# check if LineKey is covered
		if lkey in LMCoveragePerLineKey and LMCoveragePerLineKey[lkey] > 0:
			continue 
		
		# get all covered LineKeys sharing the same LineID and WeekdayType
		(LineID, twin, wtype) = lkey
		mult = 1 
		if twin >= (ZFkeys[0] + ZFkeys[-1]) / 2.0:
			mult = -1
		R = max(twin - ZFkeys[0], ZFkeys[-1] - twin)

		LineID_WType_MatchFound = False

		wtypex = wtype + 1
		while not LineID_WType_MatchFound:
			wtypex = wtypex - 1 
			if not wtypex in WDkeys:
				raise Exception("LineID %s is not covered!" % LineID)

			for i in range(1,R):
				ind = twin + (i * mult)
				if ind in ZFkeys and (LineID, ind, wtypex) in LMCoveragePerLineKey:
					DeltaDic[lkey] = -1 * LowerLimitLMperLineKey[lkey]
					DeltaDic[(LineID, ind, wtypex)] = LowerLimitLMperLineKey[lkey]
					LineID_WType_MatchFound = True
					break 
				ind = twin - (i * mult)
				if ind in ZFkeys and (LineID, ind, wtypex) in LMCoveragePerLineKey:
					DeltaDic[lkey] = -1 * LowerLimitLMperLineKey[lkey]
					DeltaDic[(LineID, ind, wtypex)] = LowerLimitLMperLineKey[lkey]
					LineID_WType_MatchFound = True
					break 
	return DeltaDic

def MergeTwoDictionaries(dic1, dic2):
	"""
	Combine the key-value pairs of two dictionaries.
	If any key is common, value of dic2 overwrites (updates) the value of dic1.
	see: https://stackoverflow.com/questions/38987/how-to-merge-two-dictionaries-in-a-single-expression
	"""
	dic3 = dic1.copy()
	dic3.update(dic2)
	return dic3


# **************************************************************************************
# List Functions
# **************************************************************************************

def GetLengthOfListOfLists(ListOfValueLists):
	"""
	Return the number of elements in a list of lists.
	For example, return 5 for [[1,2],[2,4,6]]
	"""
	NumberOfElements = 0 
	for l in range(0, len(ListOfValueLists)):
		NumberOfElements += len(ListOfValueLists[l])
	return NumberOfElements

def GetElementInListOfLists(ListOfValueLists, index):
	"""
	Get i'th element of a list of lists, like v = [[1,2],[2,4,6]]
	v[0] = 1, v[3] = 4, where index begins from 0.

	return (ElementValue, ListInd, ElementInd)
	"""
	ind = 0 
	for l in range(0, len(ListOfValueLists)):
		for j in range(0, len(ListOfValueLists[l])):
			if ind == index:
				return (ListOfValueLists[l][j], l, j)
			ind += 1 
	raise Exception("index out of range!")

def GetElementsInListOfLists(ListOfValueLists, IndexList):
	"""
	Get i'th elements of a list of lists, like v = [[1,2],[2,4,6]]
	where i in IndexList.

	return SelectedElements = [(ElementValue1, ListInd1, ElementInd1),(ElementValue2, ListInd2, ElementInd2), ...]
	"""
	SelectedElements = []
	for i in IndexList:
		SelectedElements.append(GetElementInListOfLists(ListOfValueLists, i))
	return SelectedElements

def FindValuePairInValueList(ValueList, ValuePair, MatchOption=0):
	"""
	Find value pair [a,b] in [c,b,a,d] to return [b,a]; direction (order) is important.
	Return None if value pair is not found.

	Note: Backwards search from d to c; first match is returned.

	MatchOption:
	 0: Match both directions; [a,b] matches [a,b] and [b,a]
	 1: Match only same direction; [a,b] matches only [a,b]
	-1: Match only reverse direction; [a,b] matches only [b,a]
	"""
	if type(ValueList) != type([]):
		raise Exception("ValueList must be a list!")
	if type(ValuePair) != type([]):
		raise Exception("ValuePair must be a list!")
	if len(ValuePair) != 2:
		raise Exception("List ValuePair must have 2 values!")
	if len(ValueList) < 2:
		return None 

	L = len(ValueList)
	for i in range(1,L):
		v = [ValueList[L-i-1], ValueList[L-i]]
		if MatchOption == 0:
			if set(v) == set(ValuePair):
				return v 
		elif MatchOption == 1:
			if v[0] == ValuePair[0] and v[1] == ValuePair[1]:
				return v 
		elif MatchOption == -1:
			if v[0] == ValuePair[1] and v[1] == ValuePair[0]:
				return v 
		else:
			raise Exception("Unknown match option %s !" % MatchOption)
			
	return None

def CheckIfListHasDistinctElements(ValueList):
	"""
	Return True if given value list has distinct elements like [a,b,x]; otherwise False.
	"""
	if ValueList == None: raise Exception("Null valued input list!")
	if len(ValueList) == 0: raise Exception("Empty value list!")

	if len(ValueList) == len(set(ValueList)):
		return True
	else:
		return False

def CheckMinDifference(ValueList, MinDifference):
	"""
	Return true if the difference between every possible value-pair in list >= MinDifference,
	otherwise False.
	"""
	if ValueList == None:
		raise Exception("Null-valued ValueList!")
	if len(ValueList) == 0:
		raise Exception("Empty ValueList!")
	if len(ValueList) == 1: 
		return True 

	# len(ValueList) >= 2, continue
	ValList = list(ValueList)
	ValList.sort()

	for i in range(1, len(ValList)):
		val1 = ValList[i]
		val2 = ValList[i-1]
		if abs(val1 - val2) < MinDifference:
			return False 
	return True

def ReturnListElementsWithinInterval(OrderedList, ReferenceValue, Distance, SearchMethod=1):
	"""
	Return selected elements of the ordered list within Distance from ReferenceValue.

	SearchMethod:
	1: Search forwards
	2: Search backwards
	3: Search both forwards and backwards

	Returns: (SelectedElements, IndicesOfSelectedElements)
	"""
	SelectedElements = []
	IndicesOfSelectedElements = []

	RefValue = ReferenceValue
	
	# forwards
	if SearchMethod == 1:
		for i in range(0, len(OrderedList)):
			if OrderedList[i] >= RefValue and OrderedList[i] - RefValue <= Distance: 
				SelectedElements.append(OrderedList[i])
				IndicesOfSelectedElements.append(i)

	# backwards
	if SearchMethod == 2:
		for i in range(0, len(OrderedList)):
			if OrderedList[i] <= RefValue and RefValue - OrderedList[i] <= Distance: 
				SelectedElements.append(OrderedList[i])
				IndicesOfSelectedElements.append(i)

	# both directions 
	if SearchMethod == 3:
		for i in range(0, len(OrderedList)):
			if (OrderedList[i] >= RefValue and OrderedList[i] - RefValue <= Distance) \
				or (OrderedList[i] <= RefValue and RefValue - OrderedList[i] <= Distance): 
				SelectedElements.append(OrderedList[i])
				IndicesOfSelectedElements.append(i
					)
	
	return (SelectedElements, IndicesOfSelectedElements)

def CheckExactSequenceOfValues(ValueSequence, TargetSequence):
	"""
	Check if a subsequence of ValueSequence matches TargetSequence.
	Return True (and MatchedSequence) if there is a sequence match.

	Example for a sequence match:
		ValueSequence = [1,3,5,8,10,15]
		TargetSequence = [3, None, 8, 10]
		MatchedSequence = [3, 5, 8, 10]

	A None in TargetSequence matches any value:
	TargetSequence is a value sequence like [v1, None, v2, v3, None, v4]

	Checks for a sequence match if the first value (v1) of TargetSequence
	is found in ValueSequence.

	Return: (True/False, MatchedSequence)
	"""
	if TargetSequence[0] == None:
		raise Exception("First element of TargetSequence cannot be None!")

	MatchedSequence = []

	# shortcut
	FirstTargetElement = TargetSequence[0]
	if not ValueSequence or not FirstTargetElement in ValueSequence:
		return (True, MatchedSequence)

	# FirstTargetElement is in ValueSequence, continue 
	IndexOfFirstTargetElement = ValueSequence.index(FirstTargetElement)

	# get size of overlapping sequence
	OverlappingSize = min(len(ValueSequence) -IndexOfFirstTargetElement, len(TargetSequence))
	
	for i in range(IndexOfFirstTargetElement, IndexOfFirstTargetElement + OverlappingSize):
		j = i - IndexOfFirstTargetElement
		if TargetSequence[j] != None and TargetSequence[j] != ValueSequence[i]:
			return (False, MatchedSequence)
		MatchedSequence.append(ValueSequence[i])
	
	return (True, MatchedSequence)

def GetStartTimesForTimeWindowScanning(MaxTimeDistance, MinTimeDistance, AllTimePoints, TimeInterval=30):
	"""
	Get all required time points for time window scanning.

	FistTimePoint = (MinTime in AllTimePoints) - MaxTimeDistance
	Possible NextTimePoint = FistTimePoint + TimeInterval

	check if there is a TimePoint in AllTimePoints, such that:
	TimePoint- NextTimePoint >= MinTimeDistance and TimePoint- NextTimePoint <= MaxTimeDistance 
	if no, NextTimePoint is not required. 

	return RequiredTimePoints
	"""
	if not AllTimePoints:
		return []
	
	# get sorted time points
	SortedTimePoints = list(AllTimePoints)
	SortedTimePoints.sort()

	FirstTimePoint = SortedTimePoints[0]
	LastTimePoint = SortedTimePoints[-1]

	RequiredTimePoints = []
	RequiredTimePoints.append(FirstTimePoint)

	CurTimePoint = FirstTimePoint + TimeInterval 

	while LastTimePoint - CurTimePoint >= MinTimeDistance:
		# check if there is a TimePoint in AllTimePoints, such that:
		# TimePoint- CurTimePoint >= MinTimeDistance and TimePoint- CurTimePoint <= MaxTimeDistance 
		for TimePoint in AllTimePoints:
			if TimePoint <= CurTimePoint: continue 
			if TimePoint - CurTimePoint >= MinTimeDistance and TimePoint - CurTimePoint <= MaxTimeDistance:
				RequiredTimePoints.append(CurTimePoint)
				break 
		CurTimePoint += TimeInterval

	return RequiredTimePoints

def SplitListIntoNSublists(MyList, N):
	"""
	Return a list of N sublists. N cannot be larger than the length of MyList.
	see: https://stackoverflow.com/questions/2231663/slicing-a-list-into-a-list-of-sub-lists
	"""
	if not MyList:
		return []

	if N > len(MyList):
		raise Exception("N cannot be larger than the length of MyList!")

	p = int(math.ceil(len(MyList) / (N + 0.0)))

	return [MyList[i:i+p] for i in range(0, len(MyList), p)] 

def CheckIfList1ContainsList2(List1, List2):
	"""
	Return True if List1 contains all the elements of List2; otherwise False.
	"""
	# see: https://stackoverflow.com/questions/28567328/checking-if-list-contains-all-items-from-another-list/28567420
	return set(List1) >= set(List2)

def GetAListOfDistinctLists(*lists):
	"""
	Get a list of distinct lists; eliminate lists whose elements are contained by other lists.

	Return: (ListOfDistinctLists, DistinctListInd)
	"""
	# see: https://stackoverflow.com/questions/28567328/checking-if-list-contains-all-items-from-another-list/28567420
	
	N = len(lists)
	ContainedListInd = set()

	for i in range(0,N-1):
		for j in range(i+1,N):
			if set(lists[i]) >= set(lists[j]):
				ContainedListInd.add(j)
			else:
				if set(lists[j]) >= set(lists[i]):
					ContainedListInd.add(i)

	DistinctListInd = list(set(range(0,N)).difference(ContainedListInd))
	DistinctListInd.sort()
	return ([lists[x] for x in DistinctListInd], DistinctListInd)

def SelectLargestList(*lists):
	"""
	Return the first largest list, i.e. the list with larger number of elements.
	"""
	MaxSize = 0
	LargestList = None
	
	for l in lists:
		if len(l) > MaxSize:
			MaxSize = len(l)
			LargestList = l 
	return LargestList

def GetCommonElementsOfAllLists(*lists):
	"""
	Return a list with common elements of all lists.
	""" 
	if not lists:
		return []
		
	CommonList = set(lists[0]) 

	for L in lists[1:]:
		CommonList = CommonList.intersection(set(L))
	return list(CommonList)

# **************************************************************************************
# Interval Functions
# **************************************************************************************

def GetCorrespondingValueOfInterval(ValuePerInterval, x):
	"""
	ValuePerInterval is a dictionary with an interval (2-tuple) as key:
	IntervalToValue[(xLow, xUp)] = y 

	Find the interval, and return its corresponding value y
	"""
	for key in ValuePerInterval:
		(xLow, xUp) = key 
		if xLow <= x and x <= xUp:
			return ValuePerInterval[key] 
	
	# no matching interval
	raise Exception("No matching interval was found for value %s!" % x)

def GetTotalValueOfInterval(ValuePerInterval, Interval):
	"""
	ValuePerInterval is a dictionary like:
	{
		(0,10): 5,
		(10,20): 8
	}

	Interval is a 2-tuple like (7, 15)

	TotalValue = (10-7) * 5 + (15-10) * 8

	Returns: (TotalValue, SegmentsPerInterval)
	"""
	a = Interval[0]
	b = Interval[1]

	# get segments per interval
	SegmentsPerInterval = {}
	TotalValue = 0
	for intv in ValuePerInterval:
		c = intv[0]
		d = intv[1]
		x = GetIntersectionLengthOfTwoLines(a, b, c, d)
		SegmentsPerInterval[intv] = x 
		TotalValue += x * ValuePerInterval[intv]

	return (TotalValue, SegmentsPerInterval)

def CombineIntervals(IntervalList):
	"""
	Combine (merge) overlapping intervals in a list, 
	like: [(0,5), (2,7), (6,9), (10,12)]

	see: 
	https://codereview.stackexchange.com/questions/69242/merging-overlapping-intervals
	"""
	sorted_by_lower_bound = sorted(IntervalList, key=lambda tup: tup[0])
	merged = []

	for higher in sorted_by_lower_bound:
	    if not merged:
	        merged.append(higher)
	    else:
	        lower = merged[-1]
	        # test for intersection between lower and higher:
	        # we know via sorting that lower[0] <= higher[0]
	        if higher[0] <= lower[1]:
	            upper_bound = max(lower[1], higher[1])
	            merged[-1] = (lower[0], upper_bound)  # replace by merged interval
	        else:
	            merged.append(higher)
	return merged

def ShiftIntervals(IntervalList, x):
	"""
	Shift all intervals in IntervalList by x, like:
	[(a,b), (c,d)] --> [(a+x, b+x), (c+x, d+x)]
	"""
	IntvList = []
	for intv in IntervalList:
		IntvList.append((intv[0]+x, intv[1]+x))
	return IntvList

def CheckIfValueIsAnyInterval(IntervalList, x):
	"""
	Return True if value x is in any one the the intervals in IntervalList;
	otherwise return False.
	"""
	for intv in IntervalList:
		if x >= intv[0] and x <= intv[1]: return True 
	return False

def ConvertIntervalListToSQLCondition(IntervalList, VariableName):
	"""
	Convert a given interval list like [(1,5), (7,10)] to an SQL condition:
	"(x >= 1 and x<=5) or (x >= 7 and x<=10) where VariableName = 'x'
	"""
	ANDList = []
	for intv in IntervalList:
		CondStr = "(%s >= %s and %s <= %s)" % (VariableName, intv[0], VariableName, intv[1])
		ANDList.append(CondStr)

	return " or ".join(ANDList)

# **************************************************************************************
# Route & Connection Functions
# **************************************************************************************

def PrettyStringConnectionInfo(ConnectionInfo):
	"""
	Return a well-formatted printable connection information string
	in a single line.
	"""
	CInfo = ConnectionInfo
	LineStr = '{:^9}'.format(CInfo[ConnInfoInd['line_id']]) \
		+ " " + '{:^9}'.format(CInfo[ConnInfoInd['station_from']]) \
		+ "-" + '{:^9}'.format(CInfo[ConnInfoInd['station_to']]) \
		+ " " + PrettyStringTime(CInfo[ConnInfoInd['departure_hour']], CInfo[ConnInfoInd['departure_min']]) \
		+ " - " + PrettyStringTime(CInfo[ConnInfoInd['arrival_hour']], CInfo[ConnInfoInd['arrival_min']]) \
		+ '{:>6}'.format(CInfo[ConnInfoInd['management']]) \
		+ '{:>6}'.format(CInfo[ConnInfoInd['line_category']]) \
		+ '{:>6}'.format(CInfo[ConnInfoInd['line']]) \
		+ '{:>8}'.format(CInfo[ConnInfoInd['travel_no']]) \
		+ '{:>8}'.format(CInfo[ConnInfoInd['travel_id']]) \
		+ '{:>8}'.format(CInfo[ConnInfoInd['conn_id']]) \
		+ "\n"
	return LineStr

def PrettyStringRouteInfo(RouteInfo):
	"""
	Return a well-formatted printable string with route information
	in multiple lines.
	"""
	# see https://docs.python.org/2/library/string.html

	# header string
	RouteInfoStr = " LineID   FromStat - ToStat  Depart - Arrival Mng Gattung Line TravelNo TravelID ConnectID\n" \
		+ 		   "------------------------------------------------------------------------------------------\n"
	#              " 100|S|12  8500000 - 8503000   09:30 - 09:30  None     W  None    None    None 		""

	# skip first artificial connection
	for CInfo in RouteInfo:
		RouteInfoStr += PrettyStringConnectionInfo(CInfo)
	return RouteInfoStr

def PrettyStringSegmentInfo(SegmentInfo, SegmentNr):
	"""
	Return a well-formatted printable tour segment (Reise) information 
	string in a single line.
	"""
	SInfo = SegmentInfo 
	LineIntvStart = SInfo[SegmentInfoInd['line_IntvStart']]
	LineIntvEnd = SInfo[SegmentInfoInd['line_IntvEnd']]
	StationIntvStart = SInfo[SegmentInfoInd['stat_IntvStart']]
	StationIntvEnd = SInfo[SegmentInfoInd['stat_IntvEnd']]

	LineStr = '{:>2}'.format(SegmentNr) \
		+ " " + '{:^9}'.format(SInfo[SegmentInfoInd['line_id']]) \
		+ " (" + PrettyStringTimeMin(LineIntvStart) + "-" \
		+ PrettyStringTimeMin(LineIntvEnd) \
		+ ":" + '{:>3}'.format(LineIntvEnd-LineIntvStart) + "m) " \
		+ " " + '{:^7}'.format(SInfo[SegmentInfoInd['first_station']]) \
		+ "-" + '{:^7}'.format(SInfo[SegmentInfoInd['last_station']]) \
		+ " (" + PrettyStringTimeMin(StationIntvStart) + "-" \
		+ PrettyStringTimeMin(StationIntvEnd) \
		+ ":" + '{:>3}'.format(StationIntvEnd-StationIntvStart) + "m)" \
		+ '{:>4}'.format(SInfo[SegmentInfoInd['verwaltung']]) \
		+ '{:>4}'.format(SInfo[SegmentInfoInd['gattung']]) \
		+ '{:>6}'.format(SInfo[SegmentInfoInd['linie']]) \
		+ '{:>8}'.format(SInfo[SegmentInfoInd['fahrtnum']]) \
		+ '{:>8}'.format(SInfo[SegmentInfoInd['trip_id']]) \
		+ "\n"
	return LineStr

def PrettyStringRouteSegmentsInfo(RouteSegments):
	"""
	Return a well-formatted printable string with route segments' information
	in multiple lines.
	"""
	# see https://docs.python.org/2/library/string.html

	# header string
	RouteSegInfoStr = " Nr LinieID    Line-Interval      HstVon*-HstBis   Hst-Interval 	 TU Gat. Linie FahrtNr FahrtID \n" \
		+ 		   	  "----------------------------------------------------------------------------------------------------\n"
	#              	  " 1  7.S14b   (09:12-09:20:  8m)  8503000-8503129 (09:20-09:34: 14m)  11   S    14   19433    6599"

	for SegmentNr in RouteSegments.keys():
		SegmentInfo = RouteSegments[SegmentNr]
		RouteSegInfoStr += PrettyStringSegmentInfo(SegmentInfo, SegmentNr)
	return RouteSegInfoStr	

def PrettyStringExtendedSegmentInfo(SegmentInfo, SegmentNr, MSpec=None):
	"""
	Return a well-formatted printable extended tour segment (Reise) information 
	(incl. time window) string in a single line.
	"""
	SInfo = SegmentInfo 
	LineIntvStart = SInfo[SegmentInfoInd['line_IntvStart']]
	LineIntvEnd = SInfo[SegmentInfoInd['FinalArrivalTimeOfLine']]
	StationIntvStart = SInfo[SegmentInfoInd['stat_IntvStart']]
	StationIntvEnd = SInfo[SegmentInfoInd['stat_IntvEnd']]
	TimeWindow = SInfo[SegmentInfoInd['TimeWindow']]

	MSpecStr = ""
	if MSpec: 
		MSpecStr = '{:^9}'.format("-")

	if MSpec and SegmentNr in MSpec:
		lstr = []
		if MSpec[SegmentNr][0]:
			lstr.append('L')
		if MSpec[SegmentNr][1]:
			lstr.append('AQ')
		if MSpec[SegmentNr][2]:
			lstr.append('KI')
		if lstr:
			MSpecStr = '{:^9}'.format(','.join(lstr))
		else:
			MSpecStr = '{:^9}'.format('-')

	LineStr = '{:>2}'.format(SegmentNr) \
		+ " " + '{:^9}'.format(SInfo[SegmentInfoInd['line_id']]) \
		+ " (" + PrettyStringTimeMin(LineIntvStart) + "-" \
		+ PrettyStringTimeMin(LineIntvEnd) \
		+ ":" + '{:>3}'.format(LineIntvEnd-LineIntvStart) + "m) " \
		+ " " + '{:^7}'.format(SInfo[SegmentInfoInd['first_station']]) \
		+ "-" + '{:^7}'.format(SInfo[SegmentInfoInd['last_station']]) \
		+ " (" + PrettyStringTimeMin(StationIntvStart) + "-" \
		+ PrettyStringTimeMin(StationIntvEnd) \
		+ ":" + '{:>3}'.format(StationIntvEnd-StationIntvStart) + "m)" \
		+ " " + '{:>2}'.format(TimeWindow) + " " \
		+ MSpecStr \
		+ '{:>4}'.format(SInfo[SegmentInfoInd['verwaltung']]) \
		+ '{:>4}'.format(SInfo[SegmentInfoInd['gattung']]) \
		+ '{:>6}'.format(SInfo[SegmentInfoInd['linie']]) \
		+ '{:>8}'.format(SInfo[SegmentInfoInd['fahrtnum']]) \
		+ '{:>8}'.format(SInfo[SegmentInfoInd['trip_id']]) \
		+ "\n"
	return LineStr

def PrettyStringExtendedRouteSegmentsInfo(RouteSegments, MSpec=None):
	"""
	Return a well-formatted printable string with extended route segments' information
	in multiple lines, including TimeWindow (ZF) of segment.
	"""
	# see https://docs.python.org/2/library/string.html

	# header string
	RouteSegInfoStr = None
	if MSpec:
		RouteSegInfoStr = " Nr LinieID    Line-Interval      HstVon*-HstBis   Hst-Interval 	 ZF  Measure TU Gat. Linie FahrtNr FahrtID \n" \
			+ 		   	  "-------------------------------------------------------------------------------------------------------\n"
		#                 " 1    -1     (05:15-08:19:184m)  8576937-8589934 (05:00-05:15: 15m)  1          870 NFB    63   63011    4126"

	else:
		RouteSegInfoStr = " Nr LinieID    Line-Interval      HstVon*-HstBis   Hst-Interval 	 ZF  TU Gat. Linie FahrtNr FahrtID \n" \
			+ 		   	  "-------------------------------------------------------------------------------------------------------\n"
		#                 " 1    -1     (05:15-08:19:184m)  8576937-8589934 (05:00-05:15: 15m)  1  870 NFB    63   63011    4126"

	for SegmentNr in RouteSegments.keys():
		SegmentInfo = RouteSegments[SegmentNr]
		RouteSegInfoStr += PrettyStringExtendedSegmentInfo(SegmentInfo, SegmentNr, MSpec)
	return RouteSegInfoStr	

def PrettyStringAssignmentSolution(TDVlist, TestCustomers, VariantToRoute):
	"""
	Return a well-formatting string that display an assignment (Einsatz) solution.
	"""
	SolutionInfoStr = "Test Customer            date 			VariantNr/RouteNr\n" \
		+             "-----------------------------------------------------------\n"
	
	for tdv in TDVlist:
		(t,d,v) = tdv 
		TestCustName = TestCustomers[t]
		DateStr = ConvertDateOrdinalToDateString(d)
		VariantNr = v 
		VarStr = "None/None"
		
		if v in VariantToRoute:
			VarStr = "%s/%s" % (VariantNr, VariantToRoute[v])
			
		SolutionInfoStr += '{:<25}'.format(TestCustName) \
			+ DateStr + "          " \
			+ '{:^10}'.format(VarStr) + '\n'
	
	return SolutionInfoStr

def CheckIfIdenticalRoutes(Route1, Route2):
	"""
	Return True if Route1 is identical to Route2, with all its connections.

	Created on: 22/10/2017 (in Beldibi-Antalya)
	"""
	if Route1 and not Route2:
		return False 
	if Route2 and not Route1:
		return False 	
	if len(Route1) != len(Route2):
		return False 

	for i in range(0, len(Route1)):
		conn1 = Route1[i]
		conn2 = Route2[i]
		if conn1 != conn2:
			return False 

	return True

def GetDistinctRoutes(RouteList):
	"""
	Compare each route pair in RouteList to return a list of distinct routes.

	Returns: (DistinctRoutes, RouteIDPerRouteInd)

	Route = RouteList[RouteInd]
	RouteID points to corresponding route in DistinctRoutes
	"""
	DistinctRoutes = [RouteList[0]]
	RouteIDPerRouteInd = {}
	
	for i in range(1, len(RouteList)):
		route = RouteList[i]

		for j in range(0, len(DistinctRoutes)):
			droute = DistinctRoutes[j]
			if CheckIfIdenticalRoutes(route, droute):
				RouteIDPerRouteInd[i] = j 
				break

		if not i in RouteIDPerRouteInd:
			DistinctRoutes.append(route)
			RouteIDPerRouteInd[i] = len(DistinctRoutes) - 1

	return (DistinctRoutes, RouteIDPerRouteInd)


def PrettyStringAggregateConnection(ConnInfo, AggrConnInfoIndex):
	"""
	Return a well-formatted printable aggregate connection information string
	in a single line.
	"""
	CInfo = ConnInfo
	LineStr = '{:^9}'.format(CInfo[AggrConnInfoIndex['line_id']]) \
		+ " " + '{:^9}'.format(CInfo[AggrConnInfoIndex['haltestelle_ab']]) \
		+ "-" + '{:^9}'.format(CInfo[AggrConnInfoIndex['haltestelle_an']]) \
		+ " " + PrettyStringTimeMin(CInfo[AggrConnInfoIndex['abfahrtm']]) \
		+ " - " + PrettyStringTimeMin(CInfo[AggrConnInfoIndex['ankunftm']]) \
		+ '{:>8}'.format(CInfo[AggrConnInfoIndex['verwaltung']]) \
		+ '{:>8}'.format(CInfo[AggrConnInfoIndex['gattung']]) \
		+ '{:>6}'.format(CInfo[AggrConnInfoIndex['linie']]) \
		+ '{:>8}'.format(str(CInfo[AggrConnInfoIndex['fahrtnum']])) \
		+ '{:>8}'.format(str(CInfo[AggrConnInfoIndex['fahrt_id']])) \
		+ "\n"
	return LineStr

def PrettyStringAggregatePath(PathInfo, AggrConnInfoIndex):
	"""
	Return a well-formatted printable string with aggregate path information
	in multiple lines.
	"""
	# see https://docs.python.org/2/library/string.html

	# header string
	PathInfoStr =  " LineID    VonHst - BisHst    Abfahrt-Ankunft  TU   Gattung  Linie  FahrtNr FahrtID \n" \
		+ 		   "-------------------------------------------------------------------------------------\n"
	#              " 100|S|12  8500000 - 8503000   09:30 - 09:30   None     W    None    None    None 		""

	# skip first artificial connection
	for CInfo in PathInfo:
		PathInfoStr += PrettyStringAggregateConnection(CInfo, AggrConnInfoIndex)
	return PathInfoStr


# **************************************************************************************
# Miscellaneous Functions
# **************************************************************************************

def hextobin(h):
	"""
	Convert hex string to binary string
	"""
	return bin(int(h, 16))[2:].zfill(len(h) * 4)

def bintohex(b):
	"""
	Convert binary string to hex string 
	see: http://stackoverflow.com/questions/2072351/python-conversion-from-binary-string-to-hexadecimal
	"""
	hexstr = '%0*X' % ((len(b) + 3) // 4, int(b, 2))
	return hexstr.lower()

def GetIntersectionLengthOfTwoLines(a, b, c, d):
	"""
	x coordinates of line1: (a,b) where b >= a 
	x coordinates of line2: (c,d) where d >= c 
	"""
	return max(min(d-a,b-a),0) - max(min(c-a,b-a),0)

def CheckMinDifference(ValueList, MinDifference):
	"""
	Return true if the difference between every possible value-pair in list >= MinDifference,
	otherwise False.
	"""
	if ValueList == None:
		raise Exception("Null-valued ValueList!")
	if len(ValueList) == 0:
		raise Exception("Empty ValueList!")
	if len(ValueList) == 1: 
		return True 

	# len(ValueList) >= 2, continue
	ValList = list(ValueList)
	ValList.sort()

	for i in range(1, len(ValList)):
		val1 = ValList[i]
		val2 = ValList[i-1]
		if abs(val1 - val2) < MinDifference:
			return False 
	return True

def PutToFront(ValueList, x):
	"""
	Move given value of list to front (position 0).
	x must be a list element.
	"""
	ValueList.remove(x)
	ValueList.insert(0,x)

def ConvertIntegerToBinaryString(n):
	return bin(n)

def ConvertBinaryStringToInteger(b):
	return int(b, 2)

def SelectBitOfBinaryStr(BitStr, BitPosition):
	"""
	Return p'th bit from left for the binary number b.
	p = BitPosition
	Return 0 if BitPosition > size of binary number 
	"""
	if BitPosition > len(BitStr) -2:
		return 0 
	else:
		return int(BitStr[-BitPosition])

def Count1sInBinaryStr(BitStr):
	return BitStr.count('1')

def PutToFront(ValueList, x):
	"""
	Move given value of list to front (position 0).
	x must be a list element.
	"""
	ValueList.remove(x)
	ValueList.insert(0,x)

def GetNextValue(IterObj):
    try:
		val = IterObj.next()
		return val
    except StopIteration:
        return None

def GetAllIterationValuesInAList(IterObj):
	res = []
	v = 0 
	while v != None:
		v = GetNextValue(IterObj)
		if v != None:
			res.append(v)
	return res

def SortIndex(RefValues, Ind):
	"""
	Sort index list w.r.t. reference values in ascending order
	"""
	# see: http://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list
	SortedInd = [x for (y,x) in sorted(zip(RefValues,Ind))]
	return SortedInd

def IncludeCodeFile(filename):
	# see: http://stackoverflow.com/questions/714881/how-to-include-external-python-code-to-use-in-other-files
    if os.path.exists(filename): 
        execfile(filename)

def SaveVariableToFile(Variable, Year, Month, VariableName, directory=None):
	"""
	Save any variable (list, dictionary, scalar..) into a file named:
	variable_[Year]_[Month]_[VariableName].dat

	Year: like 2016 
	Month: like 8 or 12
	VariableName: like 'RouteInfoList', any space ' ' is replaced with '_'
	directory: directory path like r'E:\Benutzer\tuncalik\Documents\MyWork_ETC'

	see:
	How can I make one python file run another? (import, execfile)
	http://stackoverflow.com/questions/7974849/how-can-i-make-one-python-file-run-another
	"""
	mydir = ''
	if directory:
		mydir = str(directory) + '/'

	filepath = mydir + 'variable_' + str(Year) + '_' + str(Month) + '_' + VariableName.replace(' ','_') + '.dat'
	
	# dump variable into file
	f = open(filepath, 'wb')
	pickle.dump(Variable, f)
	f.close()

	"""
	# OLD code: write Variable into file
	f = open(filepath ,'w')
	f.write('myvar = ')
	f.write(str(Variable))
	f.close() 
	"""

def ReadVariableFromFile(Year, Month, VariableName, directory=None):
	"""
	Read a saved variable (list, dictionary, scalar..) from a file named:
	variable_[Year]_[Month]_[VariableName].dat

	Return None if the file does not exist.

	Year: like 2016 
	Month: like 8 or 12
	VariableName: like 'RouteInfoList', any space ' ' is replaced with '_'
	directory: directory path like r'E:\Benutzer\tuncalik\Documents\MyWork_ETC'
	"""
	mydir = ''
	if directory:
		mydir = str(directory) + '/'

	filepath = mydir + 'variable_' + str(Year) + '_' + str(Month) + '_' + VariableName.replace(' ','_') + '.dat'

	# check if file exists
	if not os.path.exists(filepath):
		print "ReadVariableFromFile: File %s does not exist!" % filepath
		return None

	# load variable from file
	f = open(filepath, 'rb')
	var = pickle.load(f)
	f.close()
	return var

	"""
	# OLD code
	variables = {}
	execfile(filepath, variables)
	return variables['myvar']
	"""

def GenerateTourNumber(VariantNr, VariantToRoute, DepotIDPerRouteInd, PlanYear, PlanMonth):
	"""
	Generate (in PlanMonth) unique TourNumber for a given VariantNr, according to following rule:

	Die Tournummer ergibt sich folgendermassen:
	Zb. 111708001: ID vom Depot, Jahr, Monat, Tournummer(kann fortlaufend nummeriert werden. Es gibt keine Regel,
		dass eine bes3mmte Tour eine bestimmte Nummer hat)
	
	Created by Tunc on: 22/10/2017
	"""
	RouteInd = VariantToRoute[VariantNr] - 1
	DepotID = DepotIDPerRouteInd[RouteInd]
	TourNr = str(DepotID) + str(PlanYear)[2:4] + ("%02d" % PlanMonth) + ("%03d" % VariantNr)
	return TourNr

# **************************************************************************************
# Database Functions
# **************************************************************************************
import psycopg2

def GetAllDistinctLineIDsFromView(dbparams):
	"""
	Get all distinct line IDs from the QDABA view v_tourenplan_fahrten_linien.

	Returns: ListOfLineIDs
	"""
	# connect to QDABA DB
	con = psycopg2.connect(**dbparams)
	cur = con.cursor()
	ListOfLineIDs = []

	SQL = "SELECT distinct id_linie FROM qdababav.v_tourenplan_fahrten_linien;"
	cur.execute(SQL)

	ctr = 0 
	row = cur.fetchone()
	while row:
		ctr += 1
		lineID = row[0]
		if lineID != '-1': ListOfLineIDs.append(lineID)
		row = cur.fetchone()

	if con: con.close() 
	return ListOfLineIDs
	
def GetAllDistinctLineIDsFromTimeTable(database, dbuser):
	"""
	Get all distinct line IDs from the table timetable.

	Returns: ListOfLineIDs
	"""
	con = psycopg2.connect(database=dbase, user=dbuser) 
	cur = con.cursor()
	ListOfLineIDs = []

	SQL = "SELECT distinct linie_id FROM timetable;"
	cur.execute(SQL)

	ctr = 0 
	row = cur.fetchone()
	while row:
		ctr += 1
		lineID = row[0]
		if lineID != '-1': ListOfLineIDs.append(lineID)
		row = cur.fetchone()

	if con: con.close() 
	return ListOfLineIDs

# **************************************************************************************
# Functions to Obtain Test Customer Preferences
#
# Siehe: VerfuegbarkeitTestKunden3.py (Alex)
# **************************************************************************************

import psycopg2
import pypyodbc

def VerfuegbarkeitTK(DBparameters,PeriodBegin,PeriodEnd,project):
	'''
	Erstellt ein Dictionairy mit den Verfuegbarkeitkeiten der Testkunden, gefiltert nach Zeitraum und Projekt.
	Key: (Testkundennummer, Tag)
	Value: [(Startzeit, Endzeit),(Startzeit,Endzeit)]
	Beispiele:
		{
		(3309, 736156) : [(0, 420), (780, 1439)]
		(3301, 736149) : None
		(3345, 736151) : [(0, 780)]
		}
	Wenn Value = None ist der ganze Tag NICHT verfuegbar
	Wenn kein Eintrag hat der Testkunde an diesem Tag KEINE Einschraenkungen

	Eingaben:
	DBparameters: Zugangsdaten zur Datenbank
	PeriodBegin: Beginn des zu untersuchenden Zeitraums (z.B. date(2016,7,1) )
	PeriodEnd: Ende des zu untersuchenden Zeitraums (z.B. date(2016,7,31) )
	project: Projektname z.B.'BAV', 'SBB' oder 'RBS'

	'''
	# get a connection to database
	conn = psycopg2.connect(**DBparameters)
	cursor = conn.cursor()
	SQL = '''SELECT * FROM tp_bav.ausschlusstermin 
		WHERE datum BETWEEN '%s' AND '%s' 
		AND eingetragen_nutzer = ANY (
			SELECT anwender.id_anwender FROM tp_bav.anwender, tp_bav.anwenderanwendungsfall, tp_bav.anwendungsfall
			WHERE anwenderanwendungsfall.id_anwender = anwender.id_anwender 
			AND anwendungsfall.id_anwendungsfall = anwenderanwendungsfall.id_anwendungsfall
			AND anwendungsfalllang = '%s');''' % (PeriodBegin, PeriodEnd, project)

	cursor.execute(SQL)
	data = cursor.fetchall()


	# Datenstruktur Ausschlusstermine {(Testkundennummer, Tag): [(ZeitraumVerfuegbarkeit1),(ZeitraumVerfuegbarkeit2)]}
	Ausschlusstermine = {}

	for row in data:
		TK_NR = int(row[9])
		Date = row[1]
		DateSerial = Date.toordinal()
		# DateSerial = Date - PeriodBeginSerial + 1 # entfernt. Falls Datum als Laufende Nummer, ab PeriodBegin sein soll
		Ausschluss_Von_datetime = row[3]
		Ausschluss_Bis_datetime = row[4]
		Ausschluss_Ganzer_Tag = row[2]
		Keine_Einschraenkung = row[8]

		if Ausschluss_Von_datetime != None:
			Ausschluss_Von = Ausschluss_Von_datetime.hour * 60 + Ausschluss_Von_datetime.minute
		else:
			Ausschluss_Von = Ausschluss_Von_datetime

		if Ausschluss_Bis_datetime != None:
			Ausschluss_Bis = Ausschluss_Bis_datetime.hour * 60 + Ausschluss_Bis_datetime.minute
		else:
			Ausschluss_Bis = Ausschluss_Bis_datetime


		if Keine_Einschraenkung == True: #Frage: kommt das ueberhaupt in den Daten vor?
			Time = [(0, 23*60+59)]
		else:
			if Ausschluss_Ganzer_Tag == True:
				Time = None
			else:
				if Ausschluss_Von == None and Ausschluss_Bis != None:
					Time = [(Ausschluss_Bis, 23*60+59)]
				elif Ausschluss_Von != None and Ausschluss_Bis == None:
					Time = [(0, Ausschluss_Von)]
				else:
					if Ausschluss_Von < Ausschluss_Bis:
						Time = [(0, Ausschluss_Von),(Ausschluss_Bis, 23*60+59)]
					elif Ausschluss_Von > Ausschluss_Bis:
						Time = [(Ausschluss_Bis,Ausschluss_Von)]
					elif Ausschluss_Von == Ausschluss_Bis:
						Time = [(0, 23*60+59)] # Sollte nicht vorkommen
					else:
						Time = "Ich bin ein Fehler. Bitte schau mich genauer an"
		
		Ausschlusstermine.setdefault((TK_NR,DateSerial),Time)

	return Ausschlusstermine

def TestKunden(DBparameters,project):
	"""
	Funktion erstellt ein Dictionairy mit den Daten der Testkunden. Gefiltert nach Projekt.
	Key: Testkundennummer
	Value: Testkundenname

	Eingaben:
	DBparameters: Zugangsdaten zur Datenbank
	project: Projektname z.B.'BAV', 'SBB' oder 'RBS'

	To Do:
	Wenn Testkunden ausgeschieden sind, oder Büromitarbeiter werden sie hier trotzdem ausgegeben
	"""

	# get a connection to database
	conn = psycopg2.connect(**DBparameters)
	cursor = conn.cursor()
	##### TestkundenDaten {Testkundennummer: Name}
	# SQL_TK = '''SELECT id_anwender, vorname, name FROM tp_bav.anwender'''
	# Alternatives SQL, falls nach Projekt getrennt
	SQL_TK = '''SELECT anwender.id_anwender, anwender.vorname, anwender.name FROM tp_bav.anwender, tp_bav.anwenderanwendungsfall, tp_bav.anwendungsfall
			WHERE anwenderanwendungsfall.id_anwender = anwender.id_anwender 
			AND anwendungsfall.id_anwendungsfall = anwenderanwendungsfall.id_anwendungsfall
			AND anwendungsfalllang = '%s';''' % project
	cursor.execute(SQL_TK)
	TKdata = cursor.fetchall()
	TestkundenDaten = {}
	for TK in TKdata:
		TK_ID = int(TK[0])
		vorname = TK[1]
		nachname = TK[2]
		name = vorname + ' ' + nachname
		TestkundenDaten.setdefault(TK_ID, name)

	return TestkundenDaten

def MaxBlockTageTC(DBparameters,PeriodBegin, PeriodEnd):
	'''
	Erstellt ein Dictionairy mit der Anzahl maximal an auf einander folgenden Touren (in Tagen) je Testkunde.
	Key: Testkundennummer
	Value: Maximale Anzahl Tage

	Eingaben:
	DBparameters: Zugangsdaten zur Datenbank
	PeriodBegin: Beginn des zu untersuchenden Zeitraums (z.B. date(2016,7,1) )
	PeriodEnd: Ende des zu untersuchenden Zeitraums (z.B. date(2016,7,31) )
	'''
	conn = psycopg2.connect(**DBparameters)
	cursor = conn.cursor()
	# Blocktage (Tourenverteilung)
	SQL_BT = '''SELECT * from tp_bav.testkunden_daten
				WHERE datum BETWEEN '%s' AND '%s' ''' % (PeriodBegin, PeriodEnd)

	cursor.execute(SQL_BT)
	BTdata = cursor.fetchall()
	MaxBlockTage ={}
	AlternativeDepotTK = {}

	for row in BTdata:
		TK_ID = int(row[1])
		typ = row[2]
		wert = row[3]

		# Blocktage. Maximale Anzahl an auf einander folgenden Touren (in Tagen). {Testkundennummer: Anzahl Blocktage}
		if typ == 'tourenverteilung':
			if wert[0].isdigit() == True: 	# Eingabemoeglichkeiten: 3tourenTV, 4tourenTV, 5tourenTV
				Blocktage = int(wert[0]) 
			elif wert[0] == 'w':			# wechselTV
				Blocktage = 1
			elif wert[0] == 'e':			# egalTV
				Blocktage = 999
			else:
				print "Fehler! Eingabe entspricht nicht dem erwarteten Schema: " + str(wert)
			MaxBlockTage.setdefault(TK_ID, Blocktage)

	return MaxBlockTage

def DepotBahnhofTK():
	'''
	Erstellt ein Dictionairy mit den Depotbahnhöfen der Testkunden.
	Key: Testkundennummer
	Value: Haltestellennummer

	HINWEIS: Zugriff auf das Laufwerk O: wird benötigt, da hier die Accessdatenbank liegt
	'''

	# ACCESS_DATABASE_FILE = 'O:\\Daten\\10_Einsatzdatenbank SBB und BAV\\einsatz.mdb'
	ACCESS_DATABASE_FILE = 'E:\\Benutzer\\tuncalik\Documents\\MyWork_ETC\\PlanungTestUmgebung\\einsatz.mdb'
	
	# database connection string
	ODBC_CONN_STR = 'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=%s;' % ACCESS_DATABASE_FILE
	# connect to database
	conn = pypyodbc.connect(ODBC_CONN_STR)
	cur = conn.cursor()

	sql = '''SELECT IdTestkunde, StammDepot_NR FROM Testkunde''' 
	cur.execute(sql)
	DepotData = cur.fetchall()
	cur.commit()

	DepotBahnhof = {}
	for row in DepotData:
		TK_ID = row[0]
		Depot = row[1]
		DepotBahnhof.setdefault(TK_ID, Depot)
	return DepotBahnhof

def AlternativeDepotTK(DBparameters,PeriodBegin,PeriodEnd):
	'''
	Erstellt ein Dictionairy mit den alternativen Depotbahnhöfen der Testkunden.
	NOCH NICHT FERTIG!!!
	'''
	conn = psycopg2.connect(**DBparameters)
	cursor = conn.cursor()
	SQL_ZD = '''SELECT id_testkunde, typ, wert from tp_bav.testkunden_daten
				WHERE datum BETWEEN '%s' AND '%s' ''' % (PeriodBegin, PeriodEnd)

	cursor.execute(SQL_ZD)
	ZDdata = cursor.fetchall()

	AlternativeDepot ={}
	for row in ZDdata:
		TK_ID = int(row[0])
		typ = row[1]
		wert = row[2]
		if "ZD" in typ:
			AlternativeDepot.setdefault(TK_ID,[]).append((typ, wert))

	return AlternativeDepot

# **************************************************************************************
# itertools (Combinations, Cartesian Products)
# **************************************************************************************
import itertools as it 

def IterationLoop(IterObj, LabelStr):
	"""
	General iteration loop to display values in each iteration
	"""
	print "\nIteration Loop *******"
	ctr = 0
	while True:
	    try:
			val = IterObj.next()
			ctr += 1
			print "%s %s: %s" % (LabelStr, ctr, str(val))
	    except StopIteration:
	        break

def GetNextValue(IterObj):
    try:
		val = IterObj.next()
		return val
    except StopIteration:
        return None

def GetAllIterationValuesInAList(IterObj):
	res = []
	v = 0 
	while v != None:
		v = GetNextValue(IterObj)
		if v != None:
			res.append(v)
	return res

# test module
if __name__ == '__main__':

	# TEST GetCommonElementsOfAllLists(*lists)
	if True:
		print "TEST GetCommonElementsOfAllLists(*lists)"
		CommonList = GetCommonElementsOfAllLists([1,2,3], [2,3,4,5], [2,4,5,3], [4,5,6,7,2,3])
		print CommonList
		#quit()

	# TEST SelectLargestList
	if True:
		print "TEST SelectLargestList"
		LargestList = SelectLargestList([1,2,3], [2,3,4,5], [2,4,5], [4,5,6,7])
		print LargestList
		#quit()

	# GetTotalValueOfInterval(ValuePerInterval, Interval)
	ValuePerInterval = {
		(0,10): 	3,
		(10,20): 	5,
		(20,30): 	7,
		(30,40): 	7,
	}
	Interval = (12, 33)

	(TotalValue, SegmentsPerInterval) = GetTotalValueOfInterval(ValuePerInterval, Interval)

	print "TotalValue: %s" % TotalValue
	print "SegmentsPerInterval:"
	PrintDictionaryContent(SegmentsPerInterval)

	#quit()

	# GetWeekdaysOfMonthString(month, year, WeekdayList, DecemberOption=0)
	WeekdayList = [1,3,5]
	DecOptList = [0,1,2]

	print "test GetWeekdaysOfMonthString(month, year, WeekdayList, DecemberOption=0)"
	print "WeekdayList = %s" % str(WeekdayList)
	for DecOpt in DecOptList:
		print "-- DecOpt: %s" % DecOpt 
		print "Selected dates:"
		print GetWeekdaysOfMonthString(12, PlanYear, WeekdayList, DecemberOption=DecOpt)

	# GetWeekdaysOfMonth(month, year, WeekdayList, DecemberOption=0)
	WeekdayList = [1,3,5]
	DecOptList = [0,1,2]

	print "test GetWeekdaysOfMonth(month, year, WeekdayList, DecemberOption=0)"
	print "WeekdayList = %s" % str(WeekdayList)
	for DecOpt in DecOptList:
		print "-- DecOpt: %s" % DecOpt 
		print "Selected dates:"
		print GetWeekdaysOfMonth(12, PlanYear, WeekdayList, DecemberOption=DecOpt)

	quit()

	#GetCorrespondingValueOfInterval(ValuePerInterval, 3)
	IntervalValues = [1, 5, 10, 15, 25, 40, 60]
	print "test GetCorrespondingValueOfInterval(ValuePerInterval, x) with LineMeasurementDistributionToMonths"
	print "LineMeasurementDistributionToMonths:"
	PrintDictionaryContent(LineMeasurementDistributionToMonths)
	
	for x in IntervalValues:
		y = GetCorrespondingValueOfInterval(LineMeasurementDistributionToMonths, x)
		print "#LineMeasurements: %s, #MinMonths: %s" % (x, y)

	#quit()

	# CheckExactSequenceOfValues(ValueSequence, NextValue, TargetSequence)
	print "test CheckExactSequenceOfValues(ValueSequence, NextValue, TargetSequence)"
	ValueSequence = [1,3,5,7,9,11]
	TargetSequence = [5,None,9,11,15,17]
	(IfMatched, MatchedSequence) = CheckExactSequenceOfValues(ValueSequence, TargetSequence)
	print "ValueSequence = %s, TargetSequence = %s - If matched? %s MatchedSequence: %s" % (ValueSequence, TargetSequence, IfMatched, MatchedSequence)

	ValueSequence = [1,3,5,7,9,11,15,19,23]
	TargetSequence = [5,None,9,11,15]
	(IfMatched, MatchedSequence) = CheckExactSequenceOfValues(ValueSequence, TargetSequence)
	print "ValueSequence = %s, TargetSequence = %s - If matched? %s MatchedSequence: %s" % (ValueSequence, TargetSequence, IfMatched, MatchedSequence)

	ValueSequence = [1,3,5,7,8]
	TargetSequence = [5,None,9]
	(IfMatched, MatchedSequence) = CheckExactSequenceOfValues(ValueSequence, TargetSequence)
	print "ValueSequence = %s, TargetSequence = %s - If matched? %s MatchedSequence: %s" % (ValueSequence, TargetSequence, IfMatched, MatchedSequence)

	#quit()

	# GetWeekdaysOfMonth(month, year, WeekdayList)
	print "test GetWeekdaysOfMonth"
	y = 2016
	MonthList = [1,2,5,6,11,12]
	WeekdayLists = ([1,3,5], [6,7])

	for m in MonthList:
		for w in WeekdayLists:
			print "\nDays for month: %s, year: %s, WeekdayList: %s" % (m,y,str(w))
			print GetWeekdaysOfMonth(m, y, w)

	#quit()

	# ReturnListElementsWithinInterval(OrderedList, ReferenceValue, Distance, SearchMethod=1)
	OrderedList = range(1,18,2)
	Distance = 5
	ReferenceValue = 10
	print "test ReturnListElementsWithinInterval:"
	print "OrderedList: " + str(OrderedList)

	print "Look forward, distance = 5, ref = 10"
	(SelectedElements, IndicesOfSelectedElements) = \
		ReturnListElementsWithinInterval(OrderedList, ReferenceValue, Distance, SearchMethod=1)
	print SelectedElements
	print IndicesOfSelectedElements

	print "Look backward, distance = 5, ref = 10"
	(SelectedElements, IndicesOfSelectedElements) = \
		ReturnListElementsWithinInterval(OrderedList, ReferenceValue, Distance, SearchMethod=2)
	print SelectedElements
	print IndicesOfSelectedElements

	print "Look both directions, distance = 5, ref = 10"
	(SelectedElements, IndicesOfSelectedElements) = \
		ReturnListElementsWithinInterval(OrderedList, ReferenceValue, Distance, SearchMethod=3)
	print SelectedElements
	print IndicesOfSelectedElements

	# GetTimeWindowOfTimePoint
	TimePoints = range(0, 24*60, 60)
	print "test GetTimeWindowOfTimePoint +++"
	for tp in TimePoints:
		tw = FindTimeWindowOfTimePoint(ZF, tp)
		print "TimeWindow of TimePoint %s = %s" % (tp, tw)
	
	# test SaveRouteInfoList ***
	RouteInfoList = [1,2,3,4]
	print "SaveVariableToFile: Save RouteInfoList to current working directory..."
	year = 2016 
	month = 8
	name = 'RouteInfoList'
	SaveVariableToFile(RouteInfoList, year, month, name, directory=VariableDirectory)

	print "ReadVariableFromFile: Read RouteInfoList from current working directory..."
	var = ReadVariableFromFile(year, month, name, directory=VariableDirectory)
	print var

	print "SaveVariableToFile: Save RouteInfoList to given directory..."
	mydir = r'E:/Benutzer/tuncalik/Documents/MyWork_ETC/Python/Tunc/Planning/variables'
	year = 2016 
	month = 8
	name = 'RouteInfoList'
	SaveVariableToFile(RouteInfoList, year, month, name, mydir)

	print "ReadVariableFromFile: Read RouteInfoList from given directory..."
	var = ReadVariableFromFile(year, month, name, mydir)
	print var

	sys.exit()

	# TC Preferences *******************

	# Ausschluss nach Projekt und Datum
	project = 'BAV' # 'SBB', 'RBS'

	PeriodBegin = date(2016,7,1)
	PeriodEnd = date(2016,7,31)

	print "Ausschlusstermine:"
	Verfuegbarkeit = VerfuegbarkeitTK(QDBparameters,PeriodBegin,PeriodEnd,project)
	for key in Verfuegbarkeit:
		print str(key) + " : " + str(Verfuegbarkeit[key])

	print "Testkunden:"
	TKunden = TestKunden(QDBparameters,project)
	print TKunden

	if True:
		print "Blocktage:"
		print MaxBlockTageTC(QDBparameters,PeriodBegin, PeriodEnd)

	# print "AlternativeDepot:"
	# print AlternativeDepotTK(DBparameters,PeriodBegin,PeriodEnd)

	# Liste der Tk mit Depot: Bern, Olten, Thun, Biel (Bueropersonal entfernt, wg. Fehlermeldung)
	ListeTK=[3281, 3282, 3284, 3289, 3292, 3295, 3297, 3334, 3336, 3342]

	# ueberpruefen ob Untermenge
	TKlist = TKunden.keys() 
	print "Check if subset:"
	print set(TKlist).issuperset(set(ListeTK))

	# convert binary string to hex string
	bstr = '0000 1100 0101 1001 0000 1111 1110 0000'
	print "convert to hex binary string: %s" % bstr
	bst = bstr.replace(' ', '')
	hstr = bintohex(bst)
	print "hex string: %s" % hstr

	print "\nFindValuePairInValueList:"
	vp = [2,3]
	vl = [3,1,4,5,3,2,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp)
	print "Value List: %s" % str(vl)
	print "Value Pair: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	vl = [3,1,4,2,3,8,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp)
	print "Value List: %s" % str(vl)
	print "Value Pair: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	vl = [3,1,4,5,3,8,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp)
	print "Value List: %s" % str(vl)
	print "Value Pair: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	vl = [3,1,4,2,3,8,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp, MatchOption=1)
	print "Value List: %s" % str(vl)
	print "Value Pair, MatchOption=1: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	vl = [3,1,4,2,3,8,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp, MatchOption=-1)
	print "Value List: %s" % str(vl)
	print "Value Pair, MatchOption=-1: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	vl = [3,1,4,2,3,2,8,5,7,1,2,4,3]
	vm = FindValuePairInValueList(ValueList=vl, ValuePair=vp, MatchOption=-1)
	print "Value List: %s" % str(vl)
	print "Value Pair, MatchOption=-1: %s" % str(vp)
	print "Matched Pair: %s" % str(vm)

	sys.exit()

	# requires MS Access DB
	print "DepotBahnhof:"
	print DepotBahnhofTK()



