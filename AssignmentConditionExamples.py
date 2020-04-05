#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created on: 18.02.2020 (Tunc Ali Kütükcüoglu)
"""
Examples of Assignment Conditions (for Bosphorus Uni Students)

Script as document only, not for excecution
"""
class AssignCond:
	"""
	Class with Assignment (Einsatz) conditions
	"""

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

	MinTimeDifferenceBetweenAQMeasurements = 4
	MinTimeDifferenceBetweenAQMeasurements_explain = """
		Minimum required time interval in minutes between two AQ measurements 
		of the same station on the same day.
		Parameters: 
			MinTimeDifferenceStation = x 
			TrackCountPerStation[station] = n 		(Anzahl Gleise pro Haltestelle)
		Example: AssignCond.MinTimeDifferenceBetweenAQMeasurements: (MinTimeDifferenceStation, TrackCountPerStation)
		"""

	MinNumberOfTripsPerTC = 5 
	MinNumberOfTripsPerTC_explain = """
		Lower limit for total the number of trips per each test customer.
		Parameters: MinTripCountPerTC 
		Example: AssignCond.MinNumberOfTripsPerTC: (MinTripCountPerTC,)
		"""

	MaxNumberOfTripsPerTC = 6 
	MaxNumberOfTripsPerTC_explain = """
		Upper limit for total the number of trips per each test customer.
		Parameters: MaxTripCountPerTC 
		Example: AssignCond.MaxNumberOfTripsPerTC: (MaxTripCountPerTC,)
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

	ReturnMaxNSolutions = 11 
	ReturnMaxNSolutions_explain = """
		Limit the number of solutions to be returned in SolutionList to N.
		Parameter: MaxNumberOfSolutions
		Example: 
		AssignCond.ReturnMaxNSolutions: (5,)
		"""

	MaxSearchTimeInSeconds = 12 
	MaxSearchTimeInSeconds_explain = """
		Max search execution time in seconds.
		Return all the solutions found so far, if execution time was exceeded.
		Parameter: MaxSearchTime
		Example: 
		AssignCond.MaxSearchTimeInSeconds: (30,)
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

# Assignment (Einsatz) conditions
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

	...
}

AssignmentParameters['StartStationPerTestCustomer'] = StartStationPerTestCustomer
AssignmentParameters['LMRequirements'] = LMRequirementsAll
AssignmentParameters['RevenueLineMeasure'] = RevenueLineMeasure
AssignmentParameters['CostLineMeasure'] = CostLineMeasure
AssignmentParameters['TripCostPerTimeInterval'] = TripCostPerTimeInterval
AssignmentParameters['RouteInfoList'] = RouteInfoList
AssignmentParameters['MinTripCountPerTC'] = MinTripCountPerTC

# assignment parameters
AssignmentParameters = {
	'RouteInfoList': 					RouteInfoList,
	'TestCustomerssPerStartStation': 	TCsPerStartStation,
	'LMRequirements': 					LineMeasurementRequirementsAll,		   # remaining LM requirements for Month
	'CostLineMeasure': 					CostLineMeasure,	
	'TripCostPerTimeInterval': 			TripCostPerTimeInterval,
	'StartStationPerTestCustomer': 		StartStationPerTestCustomer,	
	'RevenueLineMeasure': 				RevenueLineMeasure,	
	'CostLineMeasure': 					CostLineMeasure,	
	'MinTripCountPerTC': 				MinTripCountPerTC,	
	'TripCostPerTimeInterval': 			TripCostPerTimeInterval,
	...			
}


# find optimal solutions, simple optimization without foresight
(AssignmentSolution, SolutionValue, LMCoverageOfSolution, IncrementalValuePerTDR) = FindOptimalAssignmentSolution(AssignmentConditions, AssignmentParameters)



