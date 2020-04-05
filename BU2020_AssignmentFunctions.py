#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on: 3.03.2020 (Tunc Ali Kütükcüoglu)
"""
Assignment Plannîng (allocation of routes to days and test customers) 
with measurement variants for each route (Messvarianten)
"""
# from pyomo.environ import *
# from pyomo.opt import SolverFactory
# from pyomo.core import Var
from random import randint
from random import shuffle
import math

import psycopg2
import sys, os

from datetime import date 
from datetime import datetime
from datetime import timedelta
import calendar
import random
# import Combinations as cmb
import itertools as it
from timeit import default_timer

from BU2019_TourSearch import *
from BU2019_BasicFunctionsLib import *
from BU2019_CentralParameters import *

#######################################################################################
# TDVlist (Assignment Solution) EVALUATION FUNCTIONS
#######################################################################################

def GetAssignedTripDaysPerTC_(TDVlist):
	"""
	Get assigned trip days for each test customer:
	AssignedTripDaysPerTC[t] = [d1, d2, d3, ...]
	"""
	AssignedTripDaysPerTC = {}
	for TDV in TDVlist:
		(t,d,v) = TDV
		if not AssignedTripDaysPerTC.has_key(t): AssignedTripDaysPerTC[t] = set()
		AssignedTripDaysPerTC[t].add(d)

	for t in AssignedTripDaysPerTC:
		AssignedTripDaysPerTC[t] = list(AssignedTripDaysPerTC[t])
		AssignedTripDaysPerTC[t].sort()
	return AssignedTripDaysPerTC

def GetLineMeasurementCountPerFahrtID_(TDVlist, DayNum):
	"""
	Get line measurement counts for each ID in a given day.
	Return dictionary LMcountPerFahrtID
	"""
	LMcountPerFahrtID = {}
	RecurringFahrtID = 0
	for TDV in TDVlist:
		(t,d,v) = TDV
		if d == DayNum:
			LMvariant = TimeIntvPerLineAndZF_PerVariant[v]
			for LineZFkey in LMvariant:
				IntervalInfoList = LMvariant[LineZFkey]
				for IntervalInfo in IntervalInfoList:
					FahrtID = IntervalInfo[0]
					if not LMcountPerFahrtID.has_key(FahrtID): LMcountPerFahrtID[FahrtID] = 0
					LMcountPerFahrtID[FahrtID] += 1
	return LMcountPerFahrtID

# new: 29.09.2016
def GetLMCoverageOfSolution(TDVlist, RouteInfoList, VariantToRoute, MSpecOfVariant):
	"""
	Get total Line Measurement (LM) coverage of all measurement variants (MSpec) 
	in the assignment (Einsatz) solution (TDV list).

	VariantToRoute[v] = r 
	MSpecOfVariant[v] = MSpec

	Returns: 
	TotalLMCoverage[(LineID, TW, WG)] = n
	"""
	if not TDVlist:
		return {}

	TotalLMCoverage = {}

	for tdv in TDVlist:
		(t,d,v) = tdv 
		RouteInfo = RouteInfoList[VariantToRoute[v] - 1]
		MSpec = MSpecOfVariant[v]
		LMCoverage = GetLMCoverageOfMeasurementSpecForGivenDay(RouteInfo, MSpec, TimeWindows, d)
		TotalLMCoverage = AddDicValues(TotalLMCoverage, LMCoverage)

	return TotalLMCoverage

# must be corrected, see CostOfVariant
def GetTotalCost(TDVlist):
	"""
	Get the total cost of all trips done by all TCs
	"""
	CostOfADay = 5 

	Cost = 0
	FirstDay = TDVlist[0][1]
	LastDay = TDVlist[-1][1]
	
	for tdv in TDVlist:
		(t,d,v) = tdv
		FirstDay = min(FirstDay, d)
		LastDay = max(LastDay, d)
		if v != None:
			Cost += CostOfVariant[v]

	TotalCost = Cost + CostOfADay*(LastDay-FirstDay+1)
	return TotalCost

# new: 27.09.2016
def GetStationMeasurementCountPerLineBundle(TDVlist):
	"""
	Get station measurement count per LineBundle, for AQ and KI.

	MCountAQ[LineBundle] = n 
	MCountKI[LineBundle] = n 
	"""
	MCountAQ = {}
	MCountKI = {}
	for TDV in TDVlist:
		(t,d,v) = TDV
		MCountAQ = AddDicValues(MCountAQ, AQCoverageOfVariant[v])
		MCountKI = AddDicValues(MCountKI, KICoverageOfVariant[v])
	return (MCountAQ, MCountKI)

# new: 27.09.2016
def GetTotalRevenues(TDVlist, CoveredLMRequirements):
	"""
	Get total revenues obtained by all measurements done by all TCs.

	Upper cap to revenues is determined by the total number of measurements 
	required by CoveredLMRequirements.
	"""
	# upper limit for the number of line measurements
	LMCountLimit = sum(CoveredLMRequirements.values())

	# LM revenues
	TotalRevenuesLM =  LMCountLimit * RevenueLineMeasure

	# SM revenues
	(MCountAQ, MCountKI) = GetStationMeasurementCountPerLineBundle(TDVlist)
	
	TotalRevenuesAQ = min(sum(MCountAQ.values()), LMCountLimit) * RevenueStationMeasure_AQ
	TotalRevenuesKI = min(sum(MCountKI.values()), LMCountLimit) * RevenueStationMeasure_KI

	TotalRevenues = TotalRevenuesLM + TotalRevenuesAQ + TotalRevenuesKI
	return TotalRevenues

# new: 27.09.2016
def obj_TotalIncome(TDVlist, CoveredLMRequirements):
	"""
	Calculate total income = total revenues - total costs
	"""
	# TotalRevenue = TotalMeasurementRevenue
	TotalRevenues = GetTotalRevenues(TDVlist, CoveredLMRequirements)
	TotalCosts = GetTotalCost(TDVlist)

	return  TotalRevenues - TotalCosts

#######################################################################################
# HELPER FUNCTIONS
#######################################################################################

def MapFittingRoutesToDaysAndTCs(TCList, DayList, TKavailability, TimeIntervalPerRoute, UnvailableDaysPerRoute, RoutesPerTC):
	"""
	Map fitting Routes to Days and Test Customers:
	Which routes fit into the time window of test customer t, on day d.

	RoutesPerTCAndDay[(t,d)] = [r1, r2, ...]

	TKavailability (Alex):
	Key: (Testkundennummer, Tag) = (t,d)
	Value: [(Startzeit, Endzeit),(Startzeit,Endzeit)]
	Beispiele:
		{
		(3309, 736156) : [(0, 420), (780, 1439)]
		(3301, 736149) : None
		(3345, 736151) : [(0, 780)]
		}
	Wenn Value = None ist der ganze Tag NICHT verfuegbar
	Wenn kein Eintrag hat der Testkunde an diesem Tag KEINE Einschraenkungen

	returns: (RoutesPerTCAndDay, FittingRoutes, FittingDays, FittingTCs)
	"""
	RoutesPerTCAndDay = {}
	R = len(TimeIntervalPerRoute)

	# routes and days that fit
	FittingRoutes = set()
	FittingDays = set()
	FittingTCs = set()

	for t in TCList:
		for d in DayList:
			RoutesPerTCAndDay[(t,d)] = []
			if (t,d) in TKavailability and TKavailability[(t,d)] == None: 
				continue
			for r in range(1, R+1):
				RouteList = []
				if t in RoutesPerTC: RouteList = RoutesPerTC[t]
				if r in RouteList:
					if d not in UnvailableDaysPerRoute[r]:
						if (t,d) not in TKavailability:
							RoutesPerTCAndDay[(t,d)].append(r)
							FittingRoutes.add(r)
							FittingDays.add(d)
							FittingTCs.add(t)
						else:
							StartMinRoute = TimeIntervalPerRoute[r][0]
							EndMinRoute = TimeIntervalPerRoute[r][1]
							# there can be multiple availability intervals in a day
							for TimeIntv in TKavailability[(t,d)]:
								StartMinTW = TimeIntv[0]
								EndMinTW = TimeIntv[1]
								if StartMinTW <= StartMinRoute and EndMinTW >= EndMinRoute:
									RoutesPerTCAndDay[(t,d)].append(r)
									FittingRoutes.add(r)
									FittingDays.add(d)
									FittingTCs.add(t)
									break 

	FittingRoutes = list(FittingRoutes)
	FittingRoutes.sort()
	FittingDays = list(FittingDays)
	FittingDays.sort()
	FittingTCs = list(FittingTCs)
	FittingTCs.sort()

	return (RoutesPerTCAndDay, FittingRoutes, FittingDays, FittingTCs)

def AddWeekdayGroupToLineAndTWKey(DicPerLineAndZF, WeekdayGroup):
	"""
	Add weekday group to key tuple (Line, TimeWindow) --> (Line, TimeWindow, WeekdayGroup)

	Note: WeekdayGroup = WeekdayGroupPerDay[d]

	returns: DicPerLineTimeWindowWeekdayGrup
	"""
	DicPerLineTimeWindowWeekdayGrup = {}

	for key in DicPerLineAndZF:
		newkey = [key[0], key[1]]
		newkey.append(WeekdayGroup)
		newkey = tuple(newkey)
		DicPerLineTimeWindowWeekdayGrup[newkey] = DicPerLineAndZF[key]

	return DicPerLineTimeWindowWeekdayGrup

def CompareLineMeasurementProfileOfRouteWithRequirements(LMRequirementMultiplicity, RouteInfo, CountLimit, ReqLineMeasureTime, \
	TimeWindows, WeekdayGroups, StartDate, EndDate):
	"""
	Compare line measurement profile (ability) of given route with line measurement (LM) requirements. 

	Matching LineKey (Line,ZF,WD) combinations are incremented in LMRequirementCount. 
	Increments up to CountLimit (for any LineKey) are counted as added-value of route.

	CommonLineKeys: Matching LineKey (Line,ZF,WD) combinations (need not be incremented)
	NewLineKeys: LineKey (Line,ZF,WD) combinations covered for the first time; i.e. incremented from 0 to 1

	LMRequirementMultiplicity = {
		(L1, 2, 11): 0
		(L2, 2, 12): 2, ... }

	Return:
	(AddedValue, LMRequirementMultiplicity, CommonLineKeys, NewLineKeys)
	"""
	TimeIntervalPerLineAndZF = GetRequiredMeasurableTimeIntervalsPerLineAndTW(RouteInfo, ReqLineMeasureTime, TimeWindows, WeekdayGroups, StartDate, EndDate, LMRequirementMultiplicity)
	(AvailableDaysRoute, UnavailableDaysRoute)= GetAvailabilityOfRoute(RouteInfo, StartDate, EndDate)
	WGroups = GetAvailableWeekDayGroups(WeekdayGroups, AvailableDaysRoute)
	AddedValue = 0
	CommonLineKeys = set()
	NewLineKeys = set()
	
	# find matching Line/ZF/WD combinations
	for dkey in TimeIntervalPerLineAndZF:
		for rkey in LMRequirementMultiplicity:
			wdgroup = rkey[2]
			if dkey[0] == rkey[0] and dkey[1] == rkey[1] and rkey[1] and wdgroup in WGroups:
				CommonLineKeys.add(rkey)
				if LMRequirementMultiplicity[rkey] < CountLimit:
					LMRequirementMultiplicity[rkey] += 1
					AddedValue += 1 
					if LMRequirementMultiplicity[rkey] == 1:
						NewLineKeys.add(rkey)

	return (AddedValue, LMRequirementMultiplicity, CommonLineKeys, NewLineKeys)

def GetUncoveredLineKeys_Line_TW_WG(LineMeasurementRequirements,LMCounter):
	"""
	Find tuples (Line,TW,WG) for which line measurement requirements are not covered.
	Return a list with uncovered tuples.

	TW: Time Window 
	WG: Weekday Group
	"""
	UncoveredKeys = []
	for key in LineMeasurementRequirements:
		if not LMCounter.has_key(key):
			UncoveredKeys.append(key)
		else:
			if LineMeasurementRequirements[key] > LMCounter[key]:
				UncoveredKeys.append(key)
	return UncoveredKeys

def GetUncoveredLineBundles(StationMeasurementRequirementsPerLB, SMCounter):
	"""
	Find line bundles (LB) for which station measurement requirements are not covered.
	Return a list with uncovered line bundles.
	"""
	UncoveredLBs = []
	for key in StationMeasurementRequirementsPerLB:
		if not SMCounter.has_key(key):
			UncoveredLBs.append(key)
		else:
			if StationMeasurementRequirementsPerLB[key] > SMCounter[key]:
				UncoveredLBs.append(key)
	return UncoveredLBs

def GetAllExcludedTDVtuples(LineKeysOfExcludedTDVtuples, TDVtuplesPerLineKey):
	"""
	Return all excluded time-fitting TDVtuples in a set whose LineKeys 
	are listed in LineKeysOfExcludedTDVtuples.

	Return set AllExcludedTDVtuples
	"""
	AllTDVtuples = set()
	if not LineKeysOfExcludedTDVtuples:
		return AllTDVtuples 

	for LineKey in LineKeysOfExcludedTDVtuples:
		if not TDVtuplesPerLineKey.has_key(LineKey):
			continue
		AllTDVtuples.union(set(TDVtuplesPerLineKey[LineKey])) 
	return AllTDVtuples

def GetAllTDVtuplesOfDayForUncoveredRequirements(day, UncoveredLineKeys, UncoveredLineBundlesAQ, UncoveredLineBundlesKI, \
	TDVtuplesPerLineKey, VariantsPerLineBundleForAQ, VariantsPerLineBundleForKI, LineKeysOfExcludedTDVtuples):
	"""
	Get a list of all possible TDV tuples of given day, 
	for uncovered line and station measurement (AQ and KI) needs.

	27.09.2016: Update for AQ and KI type station measurements + extra tuples
	"""
	TDVtuplesOfDay = set()
	IncludedVariants = set()

	# uncovered LM
	for LineKey in UncoveredLineKeys:
		(line,TW,WG) = LineKey
		TDVtuples = TDVtuplesPerLineKey[LineKey]
		TDVtuples = [tdv for tdv in TDVtuples if tdv[1] == day]		# select TDV tuples of day
		TDVtuplesOfDay = TDVtuplesOfDay.union(set(TDVtuples))

	# get all included variants
	for TDV in TDVtuplesOfDay:
		(t,d,v) = TDV 
		IncludedVariants.add(v)

	# extra TDVs for uncovered station measurements
	ExtraVariants = set()
	
	# uncovered AQ
	for LB in UncoveredLineBundlesAQ:
		if LB in VariantsPerLineBundleForAQ:
			variants = set(VariantsPerLineBundleForAQ[LB])
			if not variants.intersection(TDVtuplesOfDay):
				ExtraVariants = ExtraVariants.union(variants)

	# uncovered KI
	for LB in UncoveredLineBundlesKI:
		if LB in VariantsPerLineBundleForKI:
			variants = set(VariantsPerLineBundleForKI[LB])
			if not variants.intersection(TDVtuplesOfDay):
				ExtraVariants = ExtraVariants.union(variants)

	if ExtraVariants:
		# select TDVs with v in ExtraVariants
		ExtraTDVtuples = [tdv for tdv in TDVtuples if tdv[1] == day and tdv[2] in ExtraVariants]
		TDVtuplesOfDay = list(TDVtuplesOfDay) + ExtraTDVtuples

	# exclude TDVs (that add to already with surplus covered LineKeys?)
	AllExcludedTDVtuples = GetAllExcludedTDVtuples(LineKeysOfExcludedTDVtuples, TDVtuplesPerLineKey)
	TDVtuplesOfDay = set(TDVtuplesOfDay).difference(AllExcludedTDVtuples)
	return list(TDVtuplesOfDay)

# IterObj = it.product(*TDVtuplesPerTC_List)
def GetAllTDVtupleCombinationsOfDayForUncoveredRequirements(day, AllTDVtuplesOfDay, TClist):
	"""
	Get all possible TDV tuple combinations of day. Each combination is a distinct 
	list of TDV tuples with distinct test customers. 

	A TDV tuple with v = None may also be included in a TDV combination.
	day value must be same in all TDV tuples.
	"""
	# group TDV tuples w.r.t test customers
	TDVtuplesPerTC = {}

	for t in TClist: 
		TDVtuplesPerTC[t] = []

	for TDV in AllTDVtuplesOfDay:
		(t,d,v) = TDV 
		if d != day:
			raise Exception("Day value must be same in all TDV tuples!")
		TDVtuplesPerTC[t].append(TDV)

	for t in TDVtuplesPerTC: 
		# if not TDVtuplesPerTC[t]:			# if added on 28.09.2016
		TDVtuplesPerTC[t].append((t,day,None))
		# shuffle(TDVtuplesPerTC[t])

	# get all TDV combinations with distinct TCs in each combination (1 trip for a TC per day)
	TDVtuplesPerTC_List = []
	for t in TDVtuplesPerTC:
		TDVtuplesPerTC_List.append(TDVtuplesPerTC[t])

	# test
	# print "GetAllTDVtupleCombinationsOfDayForUncoveredRequirements.TDVtuplesPerTC_List:"
	# print TDVtuplesPerTC_List
	
	IterObj = it.product(*TDVtuplesPerTC_List)

	# test
	# for r in IterObj:
	# 	print "Day Comb:"
	# 	print list(r)
	# 	break

	# AllTDVvalueComb = GetAllIterationValuesInAList(IterObj)
	# return AllTDVvalueComb
	return IterObj

def GetAllTDVtupleCombinationsOfDay(day, UncoveredLineKeys,UncoveredLineBundlesAQ, UncoveredLineBundlesKI, \
	TDVtuplesPerLineKey, VariantsPerLineBundleForAQ, VariantsPerLineBundleForKI, TClist, LineKeysOfExcludedTDVtuples):
	"""
	
	Get all possible TDV (t,d,v) combinations for given day. 
	Each combination is a distinct list of TDV tuples with distinct test customers.

	A TDV tuple with v = None may also be included in a TDV combination.
	day value must be same in all TDV tuples.
	"""
	AllTDVtuplesOfDay = GetAllTDVtuplesOfDayForUncoveredRequirements(day, UncoveredLineKeys, UncoveredLineBundlesAQ, UncoveredLineBundlesKI, TDVtuplesPerLineKey, VariantsPerLineBundleForAQ, VariantsPerLineBundleForKI, LineKeysOfExcludedTDVtuples)
	
	# test
	# print "GetAllTDVtupleCombinationsOfDay.AllTDVtuplesOfDay:"
	# print AllTDVtuplesOfDay

	# AllTDVvalueComb = GetAllTDVtupleCombinationsOfDayForUncoveredRequirements(day, AllTDVtuplesOfDay, TClist)
	# return AllTDVvalueComb

	IterObj = GetAllTDVtupleCombinationsOfDayForUncoveredRequirements(day, AllTDVtuplesOfDay, TClist)
	return IterObj

# updated on 9.3.2020 by Tunc
def GetNumberOfTripsPerTC(TDRlist):
	"""
	Get number of assignet trips per test customer
	"""
	PlannedTripCountPerTC = {}
	for TDR in TDRlist:
		(t,d,r) = TDR
		if not PlannedTripCountPerTC.has_key(t): PlannedTripCountPerTC[t] = 0
		PlannedTripCountPerTC[t] += 1

	return PlannedTripCountPerTC

# updated on 10.3.2020 by Tunc
def UpdateLMCounter(LMCounter, LMCoverageOfRouteForGivenDay):
	"""
	Update line measurement (LM) counter w.r.t. given LMCoverageOfRoute and day d

	LMCoverageOfRoute
	LMCounter[(L,TW,WG)] = x
	"""
	"""
	WGS = GetWeekdayGroupsOfDate(WD, d)		# WG=10 is excluded, so there is only one WG for a day
	wg = WGS[0]

	LMCoverageOfRouteForGivenDay = {}
	for key in LMCoverageOfRoute:
	 	(line, twindow, wgroup) = key
	 	if wgroup == wg:
			LMCoverageOfRouteForGivenDay[key] = LMCoverageOfRoute[key]
	"""
	return AddDicValues(LMCounter, LMCoverageOfRouteForGivenDay)

def UpdateDayCounter(DayCounter, t, d):
	"""
	Update day counter: DayCounter[t] = d
	"""
	DayCtr = {}
	for tx in DayCounter:
		DayCtr[tx] = DayCounter[tx]
	DayCtr[t] = d
	return DayCtr

# new functions (after 17.02.2017) for FindOptimalAssignmentSolution()

# created on 8.3.2020 by Tunc
def GetSolutionValue(NewTDRs, SolutionTDRlist, LMCounterPerLineKey, LMRequirementsAll, LMCoverage_PerDayRoute,
	TimeIntervalPerRoute, RevenueLineMeasure, CostLineMeasure, TripCostPerTimeInterval):
	"""
	Get total solution value, considering measurement revenues and duration costs.

	Measurement counter LMCounterPerLineKey doesn't include the contribution of NewTDRs; 
	they must be updated to calculate the additional coverage with NewTDRs.

	Solution need not be complete (i.e. successfully terminated);
	just value of the current state of solution.

	CoveredLMRequirements per LineKey (LineID, TW, WG)

	Assumption: Superfluous line (per LineKey) measurements
		exceeding the required amounts do not bring any additional revenue.
	"""
	# increment LM counter
	LMCounter = IncrementLMCounter(NewTDRs, LMCounterPerLineKey, LMCoverage_PerDayRoute)

	# Line Measurement revenues & costs
	LineMeasurementCost = 0 
	LineMeasurementRevenue = 0 

	for LineKey in LMCounter:
		LineMeasurementCost += LMCounter[LineKey] * CostLineMeasure 
		LMReq = 0 
		if LineKey in LMRequirementsAll:
			LMReq = LMRequirementsAll[LineKey]
		LineMeasurementRevenue += min(LMCounter[LineKey], LineKey) * RevenueLineMeasure 

	# Route duration costs considering special hours and weekdays
	TripDurationCosts = 0
	for TDR in SolutionTDRlist + NewTDRs:
		(t,d,r) = TDR
		(StartTimeMin, EndTimeMin) = TimeIntervalPerRoute[r]
		TripInterval = (StartTimeMin, EndTimeMin) 
		(TotalIntervalValue, SegmentsPerInterval) = GetTotalValueOfInterval(TripCostPerTimeInterval, TripInterval)
		TripDurationCosts += TotalIntervalValue

	# sum up
	TotalValueOfSolution = LineMeasurementRevenue -  (LineMeasurementCost + TripDurationCosts)
	
	return TotalValueOfSolution

# created on 8.3.2020 by Tunc
def IncrementLMCounter(TDRlist, LMCounter, LMCoverage_PerDayRoute):
	"""
	Increment Line Measurement Counter by the total LM coverage of TDRlist (list of (t,d,r))
	LMCoverage_PerDayRoute[d,r] = LMCoveragePerLineKey
	"""
	for tdr in TDRlist:
		(t,d,r) = tdr
		LMCoverage = LMCoverage_PerDayRoute[d,r]
		LMCoveragePerLineKey = AddDicValues(LMCounter, LMCoverage)
	return LMCoveragePerLineKey

# created on 9.3.2020 by Tunc
def GenerateAssignmentPlanningVariables(RouteInfoList, StartStationPerTestCustomer, ReqLineMeasureTime,
	FirstDayOfMonth=PeriodBegin, LastDayOfMonth=PeriodEnd, LMRequirements=None):
	"""
	Generate all in-memory variables required for assignment planning (TDR --> (t,d,r)):
	- LMCoveragePerDayRoute[d,r] = LMCoverage (per LineKey)
	- AvailableRoutesPerTCAndDay[(t,d)] = [r1, r2, ...]
	- TimeIntervalOfRoute[r] = (DepartureMin, ArrivalMin)
	- TestCustomersPerStartStation[station] = [t1, t2, ...]
	- TravelIDListOfRoute[r] = [travelid1, travelid2, ...]

	StartStationPerTestCustomer = {
		1: 8507000, 		# Murtaza --> Bern
		2: 8504300, 		# Hatice --> Biel
		... }
	"""
	AssignmentPlanningVariables = {}
	DayList = range(FirstDayOfMonth.toordinal(), LastDayOfMonth.toordinal()+1)
	TestCustomerList = StartStationPerTestCustomer.keys()

	# TimeIntervalOfRoute
	TimeIntervalOfRoute = {}

	for r in range(0, len(RouteInfoList)):
		RouteInfo = RouteInfoList[r]
		DepartureTime = GetDepartureTimeOfTour(RouteInfo)
		ArrivalTime = GetArrivalTimeOfTour(RouteInfo)
		TimeIntervalOfRoute[r] = (DepartureTime, ArrivalTime)

	AssignmentPlanningVariables['TimeIntervalOfRoute'] = TimeIntervalOfRoute

	# LMCoveragePerDayRoute (for a given date)
	LMCoveragePerDayRoute = {}

	for r in range(0, len(RouteInfoList)):
		RouteInfo = RouteInfoList[r]
		for d in DayList:
			LMCoverage = GetLMCoverageOfRouteForGivenDay(RouteInfo, d, ReqLineMeasureTime, 
				FirstDayOfMonth, LastDayOfMonth, LMRequirements)
			LMCoveragePerDayRoute[(d,r)] = LMCoverage

	AssignmentPlanningVariables['LMCoveragePerDayRoute'] = LMCoveragePerDayRoute

	# AvailableRoutesPerTCAndDay
	AvailableRoutesPerTCAndDay = {}
	for t in TestCustomerList:
		for d in DayList:
			AvailableRoutesPerTCAndDay[(t,d)] = []

	for r in range(0, len(RouteInfoList)):
		RouteInfo = RouteInfoList[r]
		StartStation = RouteInfo[1][ConnInfoInd['station_from']]
		(AvailableDaysRoute, UnavailableDaysRoute) = GetAvailabilityOfRoute(RouteInfo, FirstDayOfMonth, LastDayOfMonth)
		for d in DayList:
			for t in TestCustomerList:
				if StartStation == StartStationPerTestCustomer[t] and d in AvailableDaysRoute:
					AvailableRoutesPerTCAndDay[(t,d)].append(r)

	AssignmentPlanningVariables['AvailableRoutesPerTCAndDay'] = AvailableRoutesPerTCAndDay

	# TravelIDListOfRoute
	TravelIDListOfRoute = {}

	for r in range(0, len(RouteInfoList)):
		RouteInfo = RouteInfoList[r]
		TravelIDListOfRoute[r] = []
		for ConnInfo in RouteInfo:
			TravelID = ConnInfo[ConnInfoInd['travel_id']]
			if not TravelID in TravelIDListOfRoute[r]:
				TravelIDListOfRoute[r].append(TravelID)

	AssignmentPlanningVariables['TravelIDListOfRoute'] = TravelIDListOfRoute

	return AssignmentPlanningVariables


#######################################################################################
# ROUTE & MSPEC VALUE
#######################################################################################

# checked: 8.3.2020 by Tunc
def GetSimpleLMRouteValue(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements, RevenueLineMeasure, TripCostPerTimeInterval):
	"""
	Get Value of Route, as a function of:
	1) Number of possible line measurements (see RevenueLineMeasure) --> LM Revenue
	2) Duration(considering different costs for different time intervals, see TripCostPerTimeInterval) --> Duration Cost
	"""
	# get possible number of LM
	(LMCoverageOfRoutePerSegment, LMCoverageOfRoutePerLineKey) = \
		GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements)

	FahrtIDSet = set() 
	for SegmentNr in LMCoverageOfRoutePerSegment:
		FahrtID = LMCoverageOfRoutePerSegment[SegmentNr][SegmentInfoInd['trip_id']]
		FahrtIDSet.add(FahrtID)

	LineMeasurementValue = RevenueLineMeasure * len(FahrtIDSet) - CostLineMeasure * len(FahrtIDSet)

	# get duration cost of route
	departure_first_station = RouteInfo[0][ConnInfoInd['departure_hour']]*60 + RouteInfo[0][ConnInfoInd['departure_min']]
	arrival_last_station = RouteInfo[-1][ConnInfoInd['arrival_hour']]*60 + RouteInfo[-1][ConnInfoInd['arrival_min']]
	TripInterval = (departure_first_station, arrival_last_station)
	(DurationCost, SegmentsPerInterval) = GetTotalValueOfInterval(TripCostPerTimeInterval, TripInterval)

	# total value 
	TotalRouteValue = LineMeasurementValue - DurationCost 
	return TotalRouteValue

# created on 8.3.2020 by Tunc
def GetDurationCostOfRoute(RouteInfo, TripCostPerTimeInterval):
	"""
	Get duration cost of a route, considering different costs for different time intervals, 
	see TripCostPerTimeInterval
	"""
	# get duration cost of route
	departure_first_station = RouteInfo[0][ConnInfoInd['departure_hour']]*60 + RouteInfo[0][ConnInfoInd['departure_min']]
	arrival_last_station = RouteInfo[-1][ConnInfoInd['arrival_hour']]*60 + RouteInfo[-1][ConnInfoInd['arrival_min']]
	TripInterval = (departure_first_station, arrival_last_station)

	(DurationCost, SegmentsPerInterval) = GetTotalValueOfInterval(TripCostPerTimeInterval, TripInterval)
	return DurationCost

#######################################################################################
# BOOLEAN TDRtupleCombOfDay & SOLUTION VALIDATION FUNCTIONS
#######################################################################################

# updated: 8.3.2020 by Tunc
def CheckNumberOfTripsForEachTC(TDRlist, MinTripCountPerTC):
	"""
	Check if a minimum number of trips assigned to each test customer (TC):
	PlannedTripCount(t) >= MinTripCount(t) for each test customer t

	Return False if PlannedTripCount <  MinTripCountPerTC[t] for any test customer t
	"""
	PlannedTripCountPerTC = {}

	for TDR in TDRlist:
		(t,d,r) = TDR
		if not PlannedTripCountPerTC.has_key(t): PlannedTripCountPerTC[t] = 0
		PlannedTripCountPerTC[t] += 1

	for t in MinTripCountPerTC:
		PlannedTripCount = 0 
		if PlannedTripCountPerTC.has_key(t): 
			PlannedTripCount = PlannedTripCountPerTC[t]
		if  PlannedTripCount < MinTripCountPerTC[t]:
			return False
	return True

# updated: 8.3.2020 by Tunc
def CheckIfTDRContributes_TO_MinNumberOfTripsForEachTC(TDR, TDRlist, MinTripCountPerTC):
	"""
	Return True if TDR contributes to the satisfaction of the solution (TDRlist) selection 
	condition as described below.

	Check if a minimum number of trips assigned to each test customer (TC):
	PlannedTripCount(t) >= MinTripCount(t) for each test customer t

	Return False if t is not a key of MinTripCountPerTC
	Return False if PlannedTripCount(t) >= MinTripCount(t)
	Return True if t is a key of MinTripCountPerTC AND PlannedTripCount(t) < MinTripCount(t)

	TDRlist does not include TDR (TDRlist before TDR)

	Created on 29.04.2017 By Tunc, Feldmeilen
	"""
	PlannedTripCountPerTC = {}
	for tdr in TDRlist:
		(t,d,r) = tdr
		if r == None: 
			continue
		if not PlannedTripCountPerTC.has_key(t): PlannedTripCountPerTC[t] = 0
		PlannedTripCountPerTC[t] += 1

	(t,d,r) = TDR
	if r == None:
		return False 
	
	if not t in MinTripCountPerTC:
		return False 

	if t in PlannedTripCountPerTC:
		# LowerLimit for t not yet reached
		if PlannedTripCountPerTC[t] < MinTripCountPerTC[t]:
			return True 
		else:
			return False

	# t NOT in PlannedTripCountPerTC
	else:
		if MinTripCountPerTC[t] > 0:
			return True 
		else:
			return False


# updated: 8.3.2020 by Tunc
def CheckMaxBlockDaysForEachTC(TDRtupleCombOfDay, TDRlist, MaxBlockDaysPerTC):
	"""
	Check if max number of allowed subsequent days with trips is not exceeded.
	Return False if max block days limit is exceeded.

	see: MaxBlockDaysPerTC[t] = 3
	"""
	SubsequentTrips = 0

	# shortcuts
	if len(TDRtupleCombOfDay) == 0:
		return True

	# check if there are MaxBlockDaysPerTC[t] times preceeding TDRtuple's 
	for TDR in TDRtupleCombOfDay:
		(t,d,r) = TDR
		if r == None: continue
		TDRlist_t = [tdr for tdr in TDRlist if tdr[0] == t and tdr[1] < d]
		
		# shortcut
		if len(TDRlist_t) < MaxBlockDaysPerTC[t]:
			continue

		TRVlist_t.sort()
		IfBlockDaysLimitExceeded = True
		for i in range(1, MaxBlockDaysPerTC[t]+1):
			tdr = TDRlist_t[-i]
			(tx,dx,rx) = tdr 
			# if not (dx == d-1 and rx != None):
			if not (dx == d-i and rx != None):
				IfBlockDaysLimitExceeded = False
		if IfBlockDaysLimitExceeded:
			return False
	return True

def CheckIfSearchTerminatesSuccessfully2(AssignmentCond, LMCounter, AQCounter, KICounter, 
	LMRequirements, AQMeasurementRequirementsPerLB, KIMeasurementRequirementsPerLB):
	"""
	Check if successful termination of solution search is reached.
	Für class AssignCond (created on 20.02.2017)
	"""	
	TotalLM = sum(LMCounter.values())

	# default termination
	if AQMeasurementRequirementsPerLB == None: AQMeasurementRequirementsPerLB = {}
	if KIMeasurementRequirementsPerLB == None: KIMeasurementRequirementsPerLB = {}

	if CheckIfEqualOrLargerDic(LMCounter, LMRequirements) and \
		CheckIfEqualOrLargerDic(AQCounter, AQMeasurementRequirementsPerLB) and \
		CheckIfEqualOrLargerDic(KICounter, KIMeasurementRequirementsPerLB):
		return True

	# termination with total LM count
	if AssignCond.TotalNumberOfLineMeasurements in AssignmentCond:
		RequiredTotalLM = AssignmentCond[AssignCond.TotalNumberOfLineMeasurements][0]
		if TotalLM >= RequiredTotalLM:
			return True 

	return False

# updated: 9.3.2020 by Tunc
def CheckIfFahrtIDMeasuredMultipleTimes(TDRlistOfDay, TravelIDListOfRoute):
	"""
	Check if a TravelID (FahrtID) is measured multiple times within a day.
	Return False if any TravelID is measured multiple times in a day.
	"""
	# shortcut
	if len(TDRlistOfDay) == 0:
		return True

	FahrtIDs = []
	for tdr in TDRlistOfDay:
		(t,d,r) = tdr
		if r == None: continue
		FahrtIDList = TravelIDListOfRoute[r]
		for fid in FahrtIDList:
			if fid in FahrtIDs:
				return False
			else:
				FahrtIDs.append(fid)
	return True

# updated: 10.3.2020 by Tunc
def CheckIfUpperLimitLMperLineKeyisExceeded(TDR, UpperLimitLMperLineKey, LMCounter, LMCoveragePerDayRoute):
	"""
	Return False if upper limit for line measurements is exceeded for any 
	line key (Line, TimeWindow, WeekdayGroup) in UpperLimitLMperLineKey.

	A missing LineKey in UpperLimitLMperLineKey means there is no upper 
	limit for this LineKey.

	TDR: Current (last) TDR tuple (t,d,v)
	TDRtuplesOfDay: TDR tuples of current (last) day without TDR 
	LMCounter: Line Measurements (per LineKey) so far, without the contribution of TDR
	LMCoveragePerDayRoute[(d,r)] = concrete LMCoverage (per LineKey) for given day 
	"""
	# update LM counter 
	LMCounterX = LMCounter.copy()
	(t,d,r) = TDR
	if r == None:
		return True 
	
	# get LM coverage of TDV per LineKey
	LMCounterX = UpdateLMCounter(LMCounterX, LMCoveragePerDayRoute[(d,r)])
	
	for LineKey in UpperLimitLMperLineKey:
		if not LineKey in LMCounterX:
			continue 
		if UpperLimitLMperLineKey[LineKey] < LMCounterX[LineKey]:
			return False 
	return True


#######################################################################################
# DEFINING ASSIGNMENT CONDITIONS WITH PARAMETERS & FUNCTIONS
#######################################################################################

# new: 18.02.2017

class AssignCond:
	"""
	Class with Assignment (Einsatz) conditions
	"""
	TerminationReasonsDic = {}
	MaxSolutionValue = None 

	IfTestSolutionSearch = False 
	MaxTotalLMReached = 0 					# max LM count reached so far

	# class constants
	MaxNumberOfTrips = 1 
	MaxNumberOfTrips_explain = """
		Upper limit for the total number of trips undertaken by all test customers 
		during the measurement period.
		Parameters: MaxTripCount = x
		Example: AssignCond.MaxNumberOfTrips: (MaxTripCount,)
		"""

	SingleFahrtIDMeasurementPerDay = 2 
	SingleFahrtIDMeasurementPerDay_explain = """
		If True (normal case), no multiple FahrtID measurements in a single day is permitted.
		Parameters: IfSingleFahrtID = True/False
		Example: AssignCond.SingleFahrtIDMeasurementPerDay: (True,)
		"""

	MaxAllowedBlockDaysPerTC = 3 
	MaxAllowedBlockDaysPerTC_explain = """
		Maximum allowed subsequent work (measurement) days for each test customer.
		Parameters: MaxBlockDaysPerTC[t] = x
		Example: AssignCond.MaxAllowedBlockDaysPerTC: (MaxBlockDaysPerTC,)
		"""

	MinNumberOfTripsPerTC = 5 
	MinNumberOfTripsPerTC_explain = """
		Lower limit for total the number of trips per each test customer.
		Parameters: MinTripCountPerTC 
		Example: AssignCond.MinNumberOfTripsPerTC: (MinTripCountPerTC,)
		"""

	MaxLineMeasurementSurplus = 8 
	MaxLineMeasurementSurplus_explain = """
		Maximum allowed measurement surplus for any line key (line, TWindow, WGroup).
		For example, if the requirement for a line key is 10, the plan can be max 
		10 + MaxLineMeasurementSurplus.
		Parameters: FirstDay, LastDay 

		Example: AssignCond.MaxLineMeasurementSurplus: (MaxLMSurplus,)
		"""

	FirstAndLastDaysOfMeasurementPeriod = 9 
	FirstAndLastDaysOfMeasurementPeriod_explain = """
		First and last days of measurement period, as ordinal date numbers like 736035.
		Parameters: FirstDay, LastDay 
		Example: 
		AssignCond.FirstAndLastDaysOfMeasurementPeriod: (FirstDay, LastDay)
		"""

	AddSolutionWithMaxValue = 10 
	AddSolutionWithMaxValue_explain = """
		Add solution to the list of solutions only if its value is 
		the highest among previously added solutions.
		Parameter: IfAddSolWithMaxValue (boolean)
		Example: 
		AssignCond.AddSolutionWithMaxValue: (True,)
		"""

	ReportDuringSolutionSearch = 13
	ReportDuringSolutionSearch_explain = """
		Report solution route search: How many solutions were found so far, etc.
		Parameter: SearchReportingIntervalInSeconds
		Example: 
		AssignCond.ReportDuringSolutionSearch: (10,)
		"""

	TestRunDuringSolutionSearch = 14 
	TestRunDuringSolutionSearch_explain = """
		Make a test run of solution search, by displaying intermediate results 
		like TDV list, LM and SM counters, termination reasons etc.
		Parameter: WaitingTimeInSeconds (waiting time between each iteration)
		Example: AssignCond.TestRunDuringSolutionSearch: (0.5,)
		"""

	TotalNumberOfLineMeasurements = 15 
	TotalNumberOfLineMeasurements_explain = """
		Check if total number of line measurements reached RequiredTotalLM;
		return true if TotalLM >= RequiredTotalLM. Criterion for successful termination.
		Parameter: RequiredTotalLM
		Example: AssignCond.TotalNumberOfLineMeasurements: (20,)
		"""

	MaxNumberOfMeasurementsPerLineKey = 16 
	MaxNumberOfMeasurementsPerLineKey_explain = """
		Check if number of line measurements are below the given upper limits
		per line key (Line, TimeWindow, WeekdayGruop). TDV selection criterion.
		Parameter: UpperLimitLMForLineKey
		Example: AssignCond.MaxNumberOfMeasurementsPerLineKey: (UpperLimitLMForLineKey,)
		"""

	MinNumberOfMeasurementsPerLineKey = 17 
	MinNumberOfMeasurementsPerLineKey_explain = """
		Check if number of line measurements are above the given upper limits
		per line key (Line, TimeWindow, WeekdayGruop). Solution selection criterion.
		Parameter: LowerLimitLMForLineKey
		Example: AssignCond.MinNumberOfMeasurementsPerLineKey: (LowerLimitLMForLineKey,)
		"""

	MaxNumberOfMeasurementsPerLine = 18 
	MaxNumberOfMeasurementsPerLine_explain = """
		Check if number of line measurements are below the given upper limits
		per LineID. TDV selection criterion.
		Parameter: UpperLimitLMForLine
		Example: AssignCond.MaxNumberOfMeasurementsPerLine: (UpperLimitLMForLine,)
		"""

	MinNumberOfMeasurementsPerLine = 19 
	MinNumberOfMeasurementsPerLine_explain = """
		Check if number of line measurements are above the given upper limits
		per LineID. Solution selection criterion.
		Parameter: LowerLimitLMForLine
		Example: AssignCond.MinNumberOfMeasurementsPerLine: (LowerLimitLMForLine,)
		"""

	@classmethod
	def ResetClassVariables(cls):
		"""
		Reset class variables, and return status variables.

		Returns:
		(StatusReport, TerminationReasons)
		"""
		# get values to return
		StatusReport = {}

		# see: http://stackoverflow.com/questions/2465921/how-to-copy-a-dictionary-and-only-edit-the-copy
		TerminationReasons = cls.TerminationReasonsDic.copy()

		# class variables
		cls.TerminationReasonsDic = {}
		cls.MaxSolutionValue = None 	
		IfTestRouteSearch = False 
		cls.MaxTotalLMReached = 0 		

		return (StatusReport, TerminationReasons)

	@classmethod
	def CheckIfTDRtupleShouldBeSelected(cls, Day, TDR, TDRlistOfDay, TDRlist, AssignConditions, Params, LMCounter):
		"""
		Determine whether the given TDR tuple (t,d,r) should be selected or rejected.

		TDR: Last (current) TDR-tuple of day (t,d,r)
		TDRlistOfDay: List of TDR-tuples of day so far, without current TDR, [(t1,d1,r1), (t2,d2,r2) ...]
		TDRlist: All TDR-tuples selected so far, without current TDR 
		Params: A dictionary of relevant condition parameters
		LMCounter: Line Measurement per LineKey so far, without current TDR
		
		Returns:
		1: True (check next condition)
		2: False (continue to the next TDRtuple in loop)
		3: None (terminate loop)
		"""
		# IfTest = cls.IfTestSolutionSearch
		IfTest = False

		# FirstAndLastDaysOfMeasurementPeriod
		if not AssignConditions.has_key(cls.FirstAndLastDaysOfMeasurementPeriod):
			raise Exception("Missing mandatory assignment condition FirstAndLastDaysOfMeasurementPeriod!")
		cond = cls.FirstAndLastDaysOfMeasurementPeriod
		(FirstDay, LastDay) = AssignConditions[cond]
		if Day == LastDay:
			IncrementDicValue(cls.TerminationReasonsDic, 'FirstAndLastDaysOfMeasurementPeriod_LastDayReached')
			if IfTest: print "--------- FirstAndLastDaysOfMeasurementPeriod_LastDayReached  ---------"
			return None 

	 	# SingleFahrtIDMeasurementPerDay
	 	if AssignConditions.has_key(cls.SingleFahrtIDMeasurementPerDay):
	 		cond = cls.SingleFahrtIDMeasurementPerDay
			parameters = AssignConditions[cond]
			IfSingleFahrtID = parameters[0]

			if IfSingleFahrtID:
				if not CheckIfFahrtIDMeasuredMultipleTimes(TDRlistOfDay + [TDR], Params['TravelIDListOfRoute']):
					IncrementDicValue(cls.TerminationReasonsDic, 'SingleFahrtIDMeasurementPerDay')
					if IfTest: print "--------- SingleFahrtIDMeasurementPerDay violated ---------"
					return False

		# MaxNumberOfMeasurementsPerLineKey
		if AssignConditions.has_key(cls.MaxNumberOfMeasurementsPerLineKey):
			cond = cls.MaxNumberOfMeasurementsPerLineKey
			parameters = AssignConditions[cond]
			UpperLimitLMperLineKey = parameters[0]
			if not CheckIfUpperLimitLMperLineKeyisExceeded(TDR, Params['UpperLimitLMperLineKey'], LMCounter, Params['LMCoveragePerDayRoute']):
				IncrementDicValue(cls.TerminationReasonsDic, 'MaxNumberOfMeasurementsPerLineKey')
				if IfTest: print "--------- MaxNumberOfMeasurementsPerLineKey exceeded ---------"
				return False

		# passed all conditions
		return True 

	@classmethod
	def CheckIfTDRlistShouldBeSelected(cls, TDRlist, AssignConditions, Params, LMCounter):
		"""
		Determine whether the solution TDRlist covers all the mandatory conditions and lower limits.
		
		Returns:
		1: True (select --> TDRlist covers all the mandatory conditions and lower limits)
		2: False (deselect --> TDRlist doesn't cover all the mandatory conditions and lower limits)
		"""
		IfTest = cls.IfTestSolutionSearch

		# MinNumberOfTripsPerTC
		if AssignConditions.has_key(cls.MinNumberOfTripsPerTC):
			cond = cls.MinNumberOfTripsPerTC
			parameters = AssignConditions[cond]
			MinTripCountPerTC = parameters[0]

			if not CheckNumberOfTripsForEachTC(TDRlist, Params['MinTripCountPerTC']):
				IncrementDicValue(cls.TerminationReasonsDic, 'MinNumberOfTripsPerTC')
				if IfTest: print "--------- MinNumberOfTripsPerTC not satisfied ---------"
				return False

		# MinNumberOfMeasurementsPerLineKey

		# MinNumberOfMeasurementsPerLine

		# passed all conditions
		return True 

	@classmethod
	def CheckIfTDRcontributesToSolutionSelectionCriteria(cls, Day, TDR, TDRlist, AssignConditions, Params, LMCounter):
		"""
		Check if the next TDR (t,d,r) of the current day contributes to solution selection 
		criteria (like MinNumberOfMeasurementsPerLine) as successful termination criteria.

		Returns:
		1: True (contributes)
		2: False (does not contribute)
		"""
		IfTest = cls.IfTestSolutionSearch

		# MinNumberOfTripsPerTC
		if AssignConditions.has_key(cls.MinNumberOfTripsPerTC):
			cond = cls.MinNumberOfTripsPerTC
			parameters = AssignConditions[cond]
			MinTripCountPerTC = parameters[0]

			if CheckIfTDRContributes_TO_MinNumberOfTripsForEachTC(TDR, TDRlist, MinTripCountPerTC):
				return True 

		# MinNumberOfMeasurementsPerLineKey


		# MinNumberOfMeasurementsPerLine


		# no contribution so far
		return False

def FindOptimalAssignmentSolution(AssignmentCond, Params):
	"""
	Finds optimal assigment solution by adding the most valuable TDR (t,d,r) assignments 
	to SolutionList one by one.

	AssignmentCond: Dictionary of all assignment conditions 
	Params: 	Dictionary of all parameters required for assignment planning

	Returns: (AssignmentSolution, SolutionValue, LMCounterPerLineKey, IncrementalValuePerTDR)
	"""
	# get all required assignment parameters
	RouteInfoList = 				Params['RouteInfoList']
	AvailableRoutesPerTCAndDay = 	Params['AvailableRoutesPerTCAndDay']
	LMCoveragePerDayRoute = 		Params['LMCoveragePerDayRoute']
	TimeIntervalOfRoute = 			Params['TimeIntervalOfRoute']
	TravelIDListOfRoute = 			Params['TravelIDListOfRoute']

	StartStationPerTestCustomer = 	Params['StartStationPerTestCustomer'] 
	LMRequirements = 				Params['LMRequirements']    # remaining LM requirements (of year) for plan Month

	RevenueLineMeasure = 			Params['RevenueLineMeasure']
	CostLineMeasure = 				Params['CostLineMeasure']
	TripCostPerTimeInterval = 		Params['TripCostPerTimeInterval']


	# list of route indices starting from 0
	RouteIndList = range(0, len(RouteInfoList))

	# Begin and End dates of Measurement Period
	(BeginDateOrd, EndDateOrd) = AssignmentCond[AssignCond.FirstAndLastDaysOfMeasurementPeriod]

	# TC list
	# assumption: A TC can be assigned to a single StartStation
	TCList = StartStationPerTestCustomer.keys()

	# AssignmentSolution is a list of TDR tuples (t,d,r)
	AssignmentSolution = []
	CurrentSolutionValue = 0

	# Counter for covered measurements (current measurement coverage of solution)
	LMCounterPerLineKey = {} 	# LineKey: (LineID, TW, WG)

	# incremental value of selected TDR
	IncrementalValuePerTDR = {}

	# pseudo-random --> deterministic solutions
	random.seed(100)
	IfTerminatedSuccessfully = False

	for d in range(BeginDateOrd, EndDateOrd+1):
		DayNr = d - BeginDateOrd + 1
		print "\nDay-%s: %s, DayOrd: %s ---------" % (DayNr, ConvertDateOrdinalToDateString(d), d)
		# TDR tuples of day = d
		TDRsOfDay = []
		ContribCount = 0 

		# shuffle TC list, in order not to assign most valuable tours always to same TCs
		TCListOfDay = list(TCList)
		shuffle(TCListOfDay)

		for t in TCListOfDay:
			# get available routes for (t,d)
			AvailableRoutesIndList = AvailableRoutesPerTCAndDay[(t,d)]

			# generate all possible TDR combinations for (t,d)
			TDR_iter = it.product([t], [d], AvailableRoutesIndList)

			# max-value TDR for (t,d)
			SelectedTDR_noncontrib = None 
			SelectedTDR_contributes = None 

			ValueOfSelectedTDR_noncontrib = None
			ValueOfSelectedTDR_contributes = None

			for tdr in TDR_iter:

				# check all TDR selection rules included by AssignCond
				IfValidTDR = AssignCond.CheckIfTDRtupleShouldBeSelected(d, tdr, TDRsOfDay, AssignmentSolution, AssignmentCond,
					Params, LMCounterPerLineKey)

				# invalid TDR
				if not IfValidTDR:
					# test
					# print "Invalid TDR tuple: %s" % str(tdr)
					continue 

				# check if TDR contributes to solution selection criteria (additional/optimal termination criteria)
				IfTDRcontributes = AssignCond.CheckIfTDRcontributesToSolutionSelectionCriteria(d, tdr, AssignmentSolution, AssignmentCond, 
					Params, LMCounterPerLineKey)
				
				if IfTDRcontributes:
					ContribCount += 1

				# select TDR with the highest (incremental) value
				# consider superfluous LineKey measurements that add no measurement value to solution
				NewTDRs = [tdr]
				SolutionValue = GetSolutionValue(NewTDRs, AssignmentSolution, LMCounterPerLineKey, LMRequirements, LMCoveragePerDayRoute,
					TimeIntervalOfRoute, RevenueLineMeasure, CostLineMeasure, TripCostPerTimeInterval)

				IncrementalValueOfTDR = SolutionValue - CurrentSolutionValue

				# test
				# print "SolutionValue = %s" % SolutionValue
				# print "IncrementalValueOfTDV = %s" % IncrementalValueOfTDV
				if IfTDRcontributes:
					if ValueOfSelectedTDR_contributes == None or IncrementalValueOfTDR > ValueOfSelectedTDR_contributes:
						SelectedTDR_contributes = tdr
						ValueOfSelectedTDR_contributes = IncrementalValueOfTDR
				else:
					if ValueOfSelectedTDR_noncontrib == None or IncrementalValueOfTDR > ValueOfSelectedTDR_noncontrib:
						SelectedTDR_noncontrib = tdr
						ValueOfSelectedTDR_noncontrib = IncrementalValueOfTDR

			# selected TDR, prefer a contributing TDR if exists
			SelectedTDR = None 
			ValueOfSelectedTDR = None
			
			if SelectedTDR_contributes:
				SelectedTDR = SelectedTDR_contributes 
				ValueOfSelectedTDR = ValueOfSelectedTDR_contributes
			else:
				if SelectedTDR_noncontrib:
					SelectedTDR = SelectedTDR_noncontrib
					ValueOfSelectedTDR = ValueOfSelectedTDR_noncontrib

			# skip to next t if a TDR is not selected
			if SelectedTDR == None:
				continue 

			# add TDR to solution
			AssignmentSolution.append(SelectedTDR)
			TDRsOfDay.append(SelectedTDR)
			CurrentSolutionValue += ValueOfSelectedTDR
			
			IncrementalValuePerTDR[SelectedTDR] = ValueOfSelectedTDR

			# update LM counter
			LMCounterPerLineKey = IncrementLMCounter([SelectedTDR], LMCounterPerLineKey, LMCoveragePerDayRoute)

			# check if assignment is complete --> terminationes successfully
			if AssignCond.CheckIfTDRlistShouldBeSelected(AssignmentSolution, AssignmentCond, Params, LMCounterPerLineKey):
				
				IfTerminatedSuccessfully = True 
				break

		# test
		print "Assignment results of day:"
		print "Current Solution: %s" % str(AssignmentSolution) 
		print "Current Solution Value: %s" % CurrentSolutionValue
		print "Current LMCounterPerLineKey (#LineKeys: %s)" % len(LMCounterPerLineKey)
		# PrintDictionaryContent(LMCounterPerLineKey)
		print "Total Number of Line Measurements: %s" % sum(LMCounterPerLineKey.values())
		print "ContribCount: %s" % ContribCount

		if IfTerminatedSuccessfully:
			break
		
	if IfTerminatedSuccessfully:
		print "Successfull termination! Assignment plan is complete."
	else:
		print "NOT terminated successfully! All termination/measurement requirements are not satisfied."
	
	return (AssignmentSolution, SolutionValue, LMCounterPerLineKey, IncrementalValuePerTDR)

#######################################################################################
# SOLUTION (TDVlist) EVALUATION FUNCTIONS
#######################################################################################

def GetMaxBlockDaysPerTC(TDVlist):
	"""
	Return max block days planned by solution TDVlist for each test customer (TC)

	Returns: MaxBlockDaysPerTC[t] = MaxBlockDays 
	"""
	# get all assigned TCs per day
	TCsPerDay = {}
	TCList = []
	for tdv in TDVlist:
		(t,d,v) = tdv 
		if v == None: continue 
		if not d in TCsPerDay: TCsPerDay[d] = []
		if not t in TCsPerDay[d]:
			TCsPerDay[d].append(t)
		if not t in TCList:
			TCList.append(t)

	# get sorted day numbers 
	DayList = TCsPerDay.keys()
	DayList.sort()

	# count MaxBlock size for each TC 
	MaxBlock = {}
	CurrentBlock = {}
	for t in TCList:
		MaxBlock[t] = 0 
		CurrentBlock[t] = 0

	for d in DayList:
		for t in TCList:
			if t in TCsPerDay[d]:
				CurrentBlock[t] += 1 
			else:
				if CurrentBlock[t] > MaxBlock[t]:
					MaxBlock[t] = CurrentBlock[t] 
				CurrentBlock[t] = 0

	return MaxBlock

def GetTripCountPerTC(TDVlist):
	"""
	Return total number of trips (assignments) per TC in plan period.

	Returns: TripCountPerTC[t] = TripCount
	"""
	TripCountPerTC = {}
	for tdv in TDVlist:
		(t,d,v) = tdv
		if v == None: continue 
		if not t in TripCountPerTC: TripCountPerTC[t] = 0 
		TripCountPerTC[t] += 1 

	return TripCountPerTC


# test module
if __name__ == '__main__':

	# CheckMeasurementMultiplicityOfAllStations(MeasureStartTimesPerStation, TimeInterval, RailCountPerStation)
	print "CheckMeasurementMultiplicityOfAllStations(MeasureStartTimesPerStation, TimeInterval, RailCountPerStation):"

	MeasureStartTimesPerStation = {
		81:	[300, 320, 400, 450, 490],
		82: [400, 450, 500, 520, 560, 580],
		83: [220, 250, 300],
		84: [300, 400, 500],
	}
	RailCountPerStation = {
		82: 4,
		83: 2,
	}
	print "MeasureStartTimesPerStation"
	PrintDictionaryContent(MeasureStartTimesPerStation)
	print "RailCountPerStation"
	PrintDictionaryContent(RailCountPerStation)

	TimeInterval = 30 
	print "TimeInterval = %s" % TimeInterval
	print CheckMeasurementMultiplicityOfAllStations(MeasureStartTimesPerStation, TimeInterval, RailCountPerStation)

	TimeInterval = 60 
	print "TimeInterval = %s" % TimeInterval
	print CheckMeasurementMultiplicityOfAllStations(MeasureStartTimesPerStation, TimeInterval, RailCountPerStation)

	TimeInterval = 100 
	print "TimeInterval = %s" % TimeInterval
	print CheckMeasurementMultiplicityOfAllStations(MeasureStartTimesPerStation, TimeInterval, RailCountPerStation)

	sys.exit()

	# CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N)
	MeasureStartTimes = [500, 520, 560, 580]
	print "CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N):"
	print "MeasureStartTimes = " + str(MeasureStartTimes)
	TimeInterval = 60 
	N = 1 
	print "TimeInterval = %s, N = %s" % (TimeInterval, N)
	print CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N)
	N = 2
	print "TimeInterval = %s, N = %s" % (TimeInterval, N)
	print CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N)
	N = 3
	print "TimeInterval = %s, N = %s" % (TimeInterval, N)
	print CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N)
	N = 3
	TimeInterval = 100
	print "TimeInterval = %s, N = %s" % (TimeInterval, N)
	print CheckStationMeasurementMultiplicity(MeasureStartTimes, TimeInterval, N)

	# sys.exit()

	# CheckIfMeasurementSpecIsLegitimate
	print "CheckIfMeasurementSpecIsLegitimate +++"

	RouteInfo = [ \
		(8500000, 8508100, None, None, None, None, None, 'W', None, 8, 0, 8, 0, None, None), 
		(8508100, 8576937, None, None, None, None, None, 'ZF', None, 8, 0, 8, 3, None, None), 
		(8576937, 8576926, 5246794, '40.052', 3936, 52010, 870, 'NFB', '52', 8, 22, 8, 23, '2|3|4|5|6|7', None), 
		(8576926, 8576927, 5246795, '40.052', 3936, 52010, 870, 'NFB', '52', 8, 23, 8, 24, '2|3|4|5|6|7', None), 
		(8576927, 8576945, 5246796, '40.052', 3936, 52010, 870, 'NFB', '52', 8, 24, 8, 26, '2|3|4|5|6|7', None), 
		(8576945, 8576946, 5246797, '40.053', 3939, 52018, 870, 'NFB', '52', 8, 26, 8, 27, '2|3|4|5|6|7', None), 
		(8576946, 8576947, 5246798, '40.052', 3936, 52010, 870, 'NFB', '52', 8, 27, 8, 28, '2|3|4|5|6|7', None), 
		(8576947, 8593531, 5246799, '40.052', 3936, 52010, 870, 'NFB', '52', 8, 28, 8, 29, '2|3|4|5|6|7', None), 
		(8593531, 8508181, None, None, None, None, None, 'ZF', None, 8, 39, 8, 41, None, None), 
		(8508181, 8508182, 1358193, '4.S7', 11626, 21730, 33, 'S', '7', 8, 52, 8, 54, '2|3|5|6|7', None), 
		(8508182, 8576937, 1358194, '4.S7', 11626, 21730, 33, 'S', '7', 8, 54, 8, 55, '2|3|5|6|7', None), 
		(8576937, 8508182, 1358188, '4.S7', 11625, 21729, 33, 'S', '7', 8, 58, 9, 2, '2|3|5|6|7', None), 
		(8508182, 8508181, 1358189, '4.S7', 11625, 21729, 33, 'S', '7', 9, 2, 9, 4, '2|3|5|6|7', None), 
		(8508181, 8508100, 1358190, '4.S7', 11625, 21729, 33, 'S', '7', 9, 4, 9, 8, '2|3|5|6|7', None)]

	print "\nRouteInfo:"
	print PrettyStringRouteInfo(RouteInfo)

	print "\nRoute segments (Reisen):"
	RouteSegments = GetRouteSegments(RouteInfo,ZF)
	print PrettyStringRouteSegmentsInfo(RouteSegments)
	
