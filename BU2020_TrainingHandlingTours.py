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
from __future__ import division
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

import csv
from matplotlib import pyplot as plt
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import numpy as np

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
	Cond.StartTimeAndDuration: (8, 0, 30, 300),		
	
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

def TEST_FindAndDisplayRoutes(RouteConditions):
	"""
	if Read_RouteInfoList_FromFile = True AND a saved variable exists --> read tours from saved variable
	Otherwise, search tours and save results (i.e. list of tours, RouteInfoList1)
	"""
	global RouteInfoList1
	print "\nFind all routes for the given route conditions..."

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

		Report=["TerminationReasons:",str(TerminationReasons)]
		FinalReport = open("CoverageForClusters.csv",'a')
		FinalReportWriter= csv.writer(FinalReport,delimiter=',',dialect='excel',lineterminator = '\n')
		FinalReportWriter.writerow(Report)
		FinalReport.close()

		# save variable to file
		#SaveVariableToFile(RouteInfoList1, PlanYear, PlanMonth, 'RouteInfoList1', directory=VariableDirectory)

	#N = 10

	# print "\nDisplay first %s routes in RouteInfoList1" % N
	# ctr = 0
	# for RouteInfo in RouteInfoList1:
	# 	ctr += 1 
	# 	if ctr > N: break
		
	# 	print "\nRoute-" + str(ctr)

	# 	# print raw RouteInfo
	# 	print "\nRaw RouteInfo:"
	# 	for conn in RouteInfo:
	# 		conn = list(conn)
	# 		conn[ConnInfoInd['trafficdays_hexcode']] = '-'
	# 		print tuple(conn)

	# 	print "\nRouteInfo:"
	# 	print PrettyStringRouteInfo(RouteInfo)
	return RouteInfoList1
# test module
if __name__ == '__main__':
	# **************************************************************************************
	# Find Some Routes
	# **************************************************************************************
	print LineSeparator
	print "Simple Travel Planning to find some routes to work with"
	print LineSeparator
	
	global AllRoutes
	AllRoutes=[]

	print "Starting to create requirement Clusters"
	requirement_clusters={ 
		0: { },
		1: { },
		2 :{ },
		3 :{ },
		4: { },
		5: { },
		6: { },
		7: { },
		8: { },
		9: { },
	}
	
	LMRequirementsAll = {
		('6.S10',2,11):   2,
		('4.S6b',2,11):   2,
		('7.S5a',2,11):   2,
		('7.S5b',2,11):   2,
		('4.S6a',2,11):   2,
		('8.S6',2,11):   2,
		('3.S6',2,11):   2,
		('3.RE2a',2,11):   2,
		('3.RE2b',2,11):   2,
		('3.S5',2,11):   2,
		('7.S14a',2,11):   2,
		('7.S14b',2,11):   2,
		('4.RE1',2,11):   2,
		('2.RE3',2,11):   2,
		('4.R5',2,11):   2,
		('4.R6',2,11):   2,
		('4.R7',2,11):   2,
		('2.S40',2,11):   2,
		('7.S3b',2,11):   2,
		('7.S3a',2,11):   2,
		('3.R1',2,11):   2,
		('3.RE4',2,11):   2,
		('3.R2',2,11):   2,
		('3.S2a',2,11):   2,
		('3.R7',2,11):   2,
		('3.R6',2,11):   2,
		('7.S25',2,11):   2,
		('3.S44c',2,11):   2,
		('7.S2a',2,11):   2,
		('7.S2b',2,11):   2,
		('1.R3',2,11):   2,
		('1.R4',2,11):   2,
		('3.S4b',2,11):   2,
		('5.RE1',2,11):   2,
		('5.S28',2,11):   2,
		('7.S16b',2,11):   2,
		('7.S16a',2,11):   2,
		('5.S9',2,11):   2,
		('3.S51',2,11):   2,
		('3.S52',2,11):   2,
		('6.S30',2,11):   2,
		('2.RE4a',2,11):   2,
		('2.RE4b',2,11):   2,
		('6.S3',2,11):   2,
		('6.S2',2,11):   2,
		('6.S9',2,11):   2,
		('2.S1',2,11):   2,
		('7.S8c',2,11):   2,
		('7.S8b',2,11):   2,
		('7.S8a',2,11):   2,
		('6.S20',2,11):   2,
		('2.S30',2,11):   2,
		('6.S25',2,11):   2,
		('6.S26',2,11):   2,
		('6.S27',2,11):   2,
		('6.S29',2,11):   2,
		('1.S2b',2,11):   2,
		('1.S2a',2,11):   2,
		('6.S23a',2,11):   2,
		('6.S23b',2,11):   2,
		('6.S41',2,11):   2,
		('2.R8',2,11):   2,
		('3.S3b',2,11):   2,
		('3.S3a',2,11):   2,
		('3.S4a',2,11):   2,
		('5.S1',2,11):   2,
		('2.R11',2,11):   2,
		('3.RE1a',2,11):   2,
		('5.S8',2,11):   2,
		('5.S3a',2,11):   2,
		('5.S3b',2,11):   2,
		('5.S3c',2,11):   2,
		('6.RE2',2,11):   2,
		('7.S7b',2,11):   2,
		('7.S7a',2,11):   2,
		('3.S2b',2,11):   2,
		('2.S9',2,11):   2,
		('3.R4b',2,11):   2,
		('3.R4a',2,11):   2,
		('7.S15b',2,11):   2,
		('7.S15a',2,11):   2,
		('2.S4b',2,11):   2,
		('2.S4a',2,11):   2,
		('7.S24b',2,11):   2,
		('7.S24c',2,11):   2,
		('7.S24a',2,11):   2,
		('2.R12',2,11):   2,
		('7.S6a',2,11):   2,
		('3.S44a',2,11):   2,
		('3.S44b',2,11):   2,
		('7.S6b',2,11):   2,
		('3.S1a',2,11):   2,
		('3.S1b',2,11):   2,
		('3.RE1b',2,11):   2,
		('2.R10',2,11):   2,
		('7.S9a',2,11):   2,
		('7.S9b',2,11):   2,
		('2.R13',2,11):   2,
		('2.R14',2,11):   2,
		('7.S12b',2,11):   2,
		('7.S12a',2,11):   2,
		('1.S3a',2,11):   2,
		('1.S3b',2,11):   2,
		('8.RE1',2,11):   2,
		('6.S10',3,11):   2,
		('4.S6b',3,11):   2,
		('7.S5a',3,11):   2,
		('7.S5b',3,11):   2,
		('4.S6a',3,11):   2,
		('8.S6',3,11):   2,
		('3.S6',3,11):   2,
		('3.RE2a',3,11):   2,
		('3.RE2b',3,11):   2,
		('3.S5',3,11):   2,
		('7.S14a',3,11):   2,
		('7.S14b',3,11):   2,
		('4.RE1',3,11):   2,
		('2.RE3',3,11):   2,
		('4.R5',3,11):   2,
		('4.R6',3,11):   2,
		('4.R7',3,11):   2,
		('2.S40',3,11):   2,
		('7.S3b',3,11):   2,
		('7.S3a',3,11):   2,
		('3.R1',3,11):   2,
		('3.RE4',3,11):   2,
		('3.R2',3,11):   2,
		('3.S2a',3,11):   2,
		('3.R7',3,11):   2,
		('3.R6',3,11):   2,
		('7.S25',3,11):   2,
		('3.S44c',3,11):   2,
		('7.S2a',3,11):   2,
		('7.S2b',3,11):   2,
		('1.R3',3,11):   2,
		('1.R4',3,11):   2,
		('3.S4b',3,11):   2,
		('5.RE1',3,11):   2,
		('5.S28',3,11):   2,
		('7.S16b',3,11):   2,
		('7.S16a',3,11):   2,
		('5.S9',3,11):   2,
		('3.S51',3,11):   2,
		('3.S52',3,11):   2,
		('6.S30',3,11):   2,
		('2.RE4a',3,11):   2,
		('2.RE4b',3,11):   2,
		('6.S3',3,11):   2,
		('6.S2',3,11):   2,
		('6.S9',3,11):   2,
		('2.S1',3,11):   2,
		('7.S8c',3,11):   2,
		('7.S8b',3,11):   2,
		('7.S8a',3,11):   2,
		('6.S20',3,11):   2,
		('2.S30',3,11):   2,
		('6.S25',3,11):   2,
		('6.S26',3,11):   2,
		('6.S27',3,11):   2,
		('6.S29',3,11):   2,
		('1.S2b',3,11):   2,
		('1.S2a',3,11):   2,
		('6.S23a',3,11):   2,
		('6.S23b',3,11):   2,
		('6.S41',3,11):   2,
		('2.R8',3,11):   2,
		('3.S3b',3,11):   2,
		('3.S3a',3,11):   2,
		('3.S4a',3,11):   2,
		('5.S1',3,11):   2,
		('2.R11',3,11):   2,
		('3.RE1a',3,11):   2,
		('5.S8',3,11):   2,
		('5.S3a',3,11):   2,
		('5.S3b',3,11):   2,
		('5.S3c',3,11):   2,
		('6.RE2',3,11):   2,
		('7.S7b',3,11):   2,
		('7.S7a',3,11):   2,
		('3.S2b',3,11):   2,
		('2.S9',3,11):   2,
		('3.R4b',3,11):   2,
		('3.R4a',3,11):   2,
		('7.S15b',3,11):   2,
		('7.S15a',3,11):   2,
		('2.S4b',3,11):   2,
		('2.S4a',3,11):   2,
		('7.S24b',3,11):   2,
		('7.S24c',3,11):   2,
		('7.S24a',3,11):   2,
		('2.R12',3,11):   2,
		('7.S6a',3,11):   2,
		('3.S44a',3,11):   2,
		('3.S44b',3,11):   2,
		('7.S6b',3,11):   2,
		('3.S1a',3,11):   2,
		('3.S1b',3,11):   2,
		('3.RE1b',3,11):   2,
		('2.R10',3,11):   2,
		('7.S9a',3,11):   2,
		('7.S9b',3,11):   2,
		('2.R13',3,11):   2,
		('2.R14',3,11):   2,
		('7.S12b',3,11):   2,
		('7.S12a',3,11):   2,
		('1.S3a',3,11):   2,
		('1.S3b',3,11):   2,
		('8.RE1',3,11):   2,
	}
	
	clusters=pd.read_excel('clusters_with_mean_coordinates.xlsx',header=None,names=["line","cluster_number"])

	for index, row in clusters.iterrows():
		for key,value in LMRequirementsAll.items():
			if key[0]==row['line']:
				cluster_number=row['cluster_number']
				requirement_clusters[int(cluster_number)][key]=value

	StartingStationList=[8507000,8503000,8501120,8505214,8507296,8517131,8500109,8505004,8508295,8502213]
	
	for i in range(10):
		print LineSeparator
		print "CLUSTER"+str(i)
		
		#Finding Appropriate Starting Station
		
		StartingStation=StartingStationList[i]
		print "Starting station for Cluster %d is %d" %(i,StartingStation)
		RequirementsSet=set(list(list(zip(*requirement_clusters[i])[0])))
		RequirementsSet=list(RequirementsSet)

		TotalSearchTimInSeconds=60*60*2
		SearchTime=len(RequirementsSet)*(TotalSearchTimInSeconds)/104
		
		SearchTimeForCSV=["SearchTimeForCluster in seconds:",SearchTime]
		StartingStationForCSV=["StartingStationForCluster:",StartingStation]

		SmallClusterIndexList=[3,5,6,7,8,9]
		if i in SmallClusterIndexList:    #6.S10'lu cluster(haritanın sağ altındaki) ve kendi yaptığım küçük clusterlar için
			RouteConditions = {
				# von und bis Haltestelle (mandatory condition)
				Cond.StartAndEndStations: (StartingStation, StartingStation), 	
				
				# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
				# determines earliest and latest arrival to end station
				Cond.StartTimeAndDuration: (8, 0, 30, 300),		
				
				# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
				Cond.MaxWaitingTimeAtStation: (25,),			
				
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
				Cond.MaxSearchTimeInSeconds: (SearchTime,),

				Cond.VisitAStationOnlyOnce: False,

				}
		else:
			RouteConditions = {
				# von und bis Haltestelle (mandatory condition)
				Cond.StartAndEndStations: (StartingStation, StartingStation), 	
				
				# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
				# determines earliest and latest arrival to end station
				Cond.StartTimeAndDuration: (8, 0, 30, 300),		
				
				# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
				Cond.MaxWaitingTimeAtStation: (25,),			
				
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
				Cond.MaxSearchTimeInSeconds: (SearchTime,),

				Cond.VisitAStationOnlyOnce: True,

				}
		FoundRoutes=TEST_FindAndDisplayRoutes(RouteConditions)
		print "Requirements for Cluster"+str(i)
		PrintDictionaryContent(requirement_clusters[i])
		RequirementForCluster=[]
		Cluster_ReqCov=["Cluster"+str(i),"Requirements"]
		RequirementForCluster.append(Cluster_ReqCov)
		for key,value in requirement_clusters[i].items():
			# Put the key in the first column for each key in the dictionary
			csv_row=[]
			csv_row.append(str(key))
			csv_row.append(value)
			RequirementForCluster.append(csv_row)
		
		if i==0:
			RequirementForClusterFile = open("CoverageForClusters.csv",'wb')
			RequirementForClusterFileWriter= csv.writer(RequirementForClusterFile,delimiter=',', dialect='excel',lineterminator = '\n')
			RequirementForClusterFileWriter.writerow(StartingStationForCSV)
			RequirementForClusterFileWriter.writerow(SearchTimeForCSV)
			RequirementForClusterFileWriter.writerows(RequirementForCluster)
			RequirementForClusterFile.close()
		else:
			RequirementForClusterFile = open("CoverageForClusters.csv",'a')
			RequirementForClusterFileWriter= csv.writer(RequirementForClusterFile,delimiter=',', dialect='excel',lineterminator = '\n')
			RequirementForClusterFileWriter.writerow(StartingStationForCSV)
			RequirementForClusterFileWriter.writerow(SearchTimeForCSV)
			RequirementForClusterFileWriter.writerows(RequirementForCluster)
			RequirementForClusterFile.close()

		print 
		print "Coverage for Cluster"+str(i)
		LMCoverageTotal = {}
		for RouteInfo in FoundRoutes:
			(LMCoveragePerSegment, LMCoveragePerLineKey) = \
				GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)
			
			LMCoverageTotal = AddDicValues(LMCoverageTotal, LMCoveragePerLineKey)
		PrintDictionaryContent(LMCoverageTotal)
		CoverageForCluster=[]
		Cluster_ReqCov=["Cluster"+str(i),"Coverage"]
		CoverageForCluster.append(Cluster_ReqCov)
		for key,value in LMCoverageTotal.items():
			# Put the key in the first column for each key in the dictionary
			csv_row=[]
			csv_row.append(str(key))
			csv_row.append(value)
			CoverageForCluster.append(csv_row)
		
		CoverageForClusterFile = open("CoverageForClusters.csv",'a')
		CoverageForClusterFileWriter= csv.writer(CoverageForClusterFile,delimiter=',', dialect='excel',lineterminator = '\n')
		CoverageForClusterFileWriter.writerows(CoverageForCluster)
		CoverageForClusterFile.close()

		AllRoutes.extend(FoundRoutes)

	print LineSeparator
	print "Evaluate tours"
	print LineSeparator

	print "All Routes is a list that contains %s routes." % len(AllRoutes)

	# **************************************************************************************
	# Line Measurement (LM) Coverage of Routes
	# **************************************************************************************
	print LineSeparator 
	print "Line Measurement (LM) Coverage of Routes"
	print LineSeparator

	# In order to calculate the Line Measurement (LM) coverage of a route,
	# we need to have first LMRequirementsAll per LineKey (LineID, TimeWindow, WeekdayGroup):
	
	LMRequirementsAll = {
		('6.S10',2,11):   2,
		('4.S6b',2,11):   2,
		('7.S5a',2,11):   2,
		('7.S5b',2,11):   2,
		('4.S6a',2,11):   2,
		('8.S6',2,11):   2,
		('3.S6',2,11):   2,
		('3.RE2a',2,11):   2,
		('3.RE2b',2,11):   2,
		('3.S5',2,11):   2,
		('7.S14a',2,11):   2,
		('7.S14b',2,11):   2,
		('4.RE1',2,11):   2,
		('2.RE3',2,11):   2,
		('4.R5',2,11):   2,
		('4.R6',2,11):   2,
		('4.R7',2,11):   2,
		('2.S40',2,11):   2,
		('7.S3b',2,11):   2,
		('7.S3a',2,11):   2,
		('3.R1',2,11):   2,
		('3.RE4',2,11):   2,
		('3.R2',2,11):   2,
		('3.S2a',2,11):   2,
		('3.R7',2,11):   2,
		('3.R6',2,11):   2,
		('7.S25',2,11):   2,
		('3.S44c',2,11):   2,
		('7.S2a',2,11):   2,
		('7.S2b',2,11):   2,
		('1.R3',2,11):   2,
		('1.R4',2,11):   2,
		('3.S4b',2,11):   2,
		('5.RE1',2,11):   2,
		('5.S28',2,11):   2,
		('7.S16b',2,11):   2,
		('7.S16a',2,11):   2,
		('5.S9',2,11):   2,
		('3.S51',2,11):   2,
		('3.S52',2,11):   2,
		('6.S30',2,11):   2,
		('2.RE4a',2,11):   2,
		('2.RE4b',2,11):   2,
		('6.S3',2,11):   2,
		('6.S2',2,11):   2,
		('6.S9',2,11):   2,
		('2.S1',2,11):   2,
		('7.S8c',2,11):   2,
		('7.S8b',2,11):   2,
		('7.S8a',2,11):   2,
		('6.S20',2,11):   2,
		('2.S30',2,11):   2,
		('6.S25',2,11):   2,
		('6.S26',2,11):   2,
		('6.S27',2,11):   2,
		('6.S29',2,11):   2,
		('1.S2b',2,11):   2,
		('1.S2a',2,11):   2,
		('6.S23a',2,11):   2,
		('6.S23b',2,11):   2,
		('6.S41',2,11):   2,
		('2.R8',2,11):   2,
		('3.S3b',2,11):   2,
		('3.S3a',2,11):   2,
		('3.S4a',2,11):   2,
		('5.S1',2,11):   2,
		('2.R11',2,11):   2,
		('3.RE1a',2,11):   2,
		('5.S8',2,11):   2,
		('5.S3a',2,11):   2,
		('5.S3b',2,11):   2,
		('5.S3c',2,11):   2,
		('6.RE2',2,11):   2,
		('7.S7b',2,11):   2,
		('7.S7a',2,11):   2,
		('3.S2b',2,11):   2,
		('2.S9',2,11):   2,
		('3.R4b',2,11):   2,
		('3.R4a',2,11):   2,
		('7.S15b',2,11):   2,
		('7.S15a',2,11):   2,
		('2.S4b',2,11):   2,
		('2.S4a',2,11):   2,
		('7.S24b',2,11):   2,
		('7.S24c',2,11):   2,
		('7.S24a',2,11):   2,
		('2.R12',2,11):   2,
		('7.S6a',2,11):   2,
		('3.S44a',2,11):   2,
		('3.S44b',2,11):   2,
		('7.S6b',2,11):   2,
		('3.S1a',2,11):   2,
		('3.S1b',2,11):   2,
		('3.RE1b',2,11):   2,
		('2.R10',2,11):   2,
		('7.S9a',2,11):   2,
		('7.S9b',2,11):   2,
		('2.R13',2,11):   2,
		('2.R14',2,11):   2,
		('7.S12b',2,11):   2,
		('7.S12a',2,11):   2,
		('1.S3a',2,11):   2,
		('1.S3b',2,11):   2,
		('8.RE1',2,11):   2,
		('6.S10',3,11):   2,
		('4.S6b',3,11):   2,
		('7.S5a',3,11):   2,
		('7.S5b',3,11):   2,
		('4.S6a',3,11):   2,
		('8.S6',3,11):   2,
		('3.S6',3,11):   2,
		('3.RE2a',3,11):   2,
		('3.RE2b',3,11):   2,
		('3.S5',3,11):   2,
		('7.S14a',3,11):   2,
		('7.S14b',3,11):   2,
		('4.RE1',3,11):   2,
		('2.RE3',3,11):   2,
		('4.R5',3,11):   2,
		('4.R6',3,11):   2,
		('4.R7',3,11):   2,
		('2.S40',3,11):   2,
		('7.S3b',3,11):   2,
		('7.S3a',3,11):   2,
		('3.R1',3,11):   2,
		('3.RE4',3,11):   2,
		('3.R2',3,11):   2,
		('3.S2a',3,11):   2,
		('3.R7',3,11):   2,
		('3.R6',3,11):   2,
		('7.S25',3,11):   2,
		('3.S44c',3,11):   2,
		('7.S2a',3,11):   2,
		('7.S2b',3,11):   2,
		('1.R3',3,11):   2,
		('1.R4',3,11):   2,
		('3.S4b',3,11):   2,
		('5.RE1',3,11):   2,
		('5.S28',3,11):   2,
		('7.S16b',3,11):   2,
		('7.S16a',3,11):   2,
		('5.S9',3,11):   2,
		('3.S51',3,11):   2,
		('3.S52',3,11):   2,
		('6.S30',3,11):   2,
		('2.RE4a',3,11):   2,
		('2.RE4b',3,11):   2,
		('6.S3',3,11):   2,
		('6.S2',3,11):   2,
		('6.S9',3,11):   2,
		('2.S1',3,11):   2,
		('7.S8c',3,11):   2,
		('7.S8b',3,11):   2,
		('7.S8a',3,11):   2,
		('6.S20',3,11):   2,
		('2.S30',3,11):   2,
		('6.S25',3,11):   2,
		('6.S26',3,11):   2,
		('6.S27',3,11):   2,
		('6.S29',3,11):   2,
		('1.S2b',3,11):   2,
		('1.S2a',3,11):   2,
		('6.S23a',3,11):   2,
		('6.S23b',3,11):   2,
		('6.S41',3,11):   2,
		('2.R8',3,11):   2,
		('3.S3b',3,11):   2,
		('3.S3a',3,11):   2,
		('3.S4a',3,11):   2,
		('5.S1',3,11):   2,
		('2.R11',3,11):   2,
		('3.RE1a',3,11):   2,
		('5.S8',3,11):   2,
		('5.S3a',3,11):   2,
		('5.S3b',3,11):   2,
		('5.S3c',3,11):   2,
		('6.RE2',3,11):   2,
		('7.S7b',3,11):   2,
		('7.S7a',3,11):   2,
		('3.S2b',3,11):   2,
		('2.S9',3,11):   2,
		('3.R4b',3,11):   2,
		('3.R4a',3,11):   2,
		('7.S15b',3,11):   2,
		('7.S15a',3,11):   2,
		('2.S4b',3,11):   2,
		('2.S4a',3,11):   2,
		('7.S24b',3,11):   2,
		('7.S24c',3,11):   2,
		('7.S24a',3,11):   2,
		('2.R12',3,11):   2,
		('7.S6a',3,11):   2,
		('3.S44a',3,11):   2,
		('3.S44b',3,11):   2,
		('7.S6b',3,11):   2,
		('3.S1a',3,11):   2,
		('3.S1b',3,11):   2,
		('3.RE1b',3,11):   2,
		('2.R10',3,11):   2,
		('7.S9a',3,11):   2,
		('7.S9b',3,11):   2,
		('2.R13',3,11):   2,
		('2.R14',3,11):   2,
		('7.S12b',3,11):   2,
		('7.S12a',3,11):   2,
		('1.S3a',3,11):   2,
		('1.S3b',3,11):   2,
		('8.RE1',3,11):   2,
	}
	
	LMCoverageTotal = {}
	RouteCosts = {}
	RouteInd=1
	Routes = {}

	for RouteInfo in AllRoutes:
		RouteName='Route' + str(RouteInd)
		
		if RouteName not in Routes : 
			Routes[RouteName]={}
		
		(LMCoveragePerSegment, LMCoveragePerLineKey) = \
			GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)
		
		if len(LMCoveragePerLineKey)>0:
			RouteInd = RouteInd+1
			for key,value in LMCoveragePerLineKey.items():
				# Put the key in the first column for each key in the dictionary
				Routes[RouteName][str(key)]=value
			departure_first_station = RouteInfo[0][ConnInfoInd['departure_hour']]*60 + RouteInfo[0][ConnInfoInd['departure_min']]
			arrival_last_station = RouteInfo[-1][ConnInfoInd['arrival_hour']]*60 + RouteInfo[-1][ConnInfoInd['arrival_min']]
			routeDur=arrival_last_station-departure_first_station
			RouteCosts[RouteName]=routeDur

		LMCoverageTotal = AddDicValues(LMCoverageTotal, LMCoveragePerLineKey)
	
	print "\nLM Coverage of all routes in AllRoutes (#LineKeys: %s)" % len(LMCoverageTotal)
	PrintDictionaryContent(LMCoverageTotal)

	totalReq=0
	totalCov=0

	for var in LMRequirementsAll:
		totalReq += LMRequirementsAll.get(var,"")

	for var in LMRequirementsAll:

		if LMCoverageTotal.get(var,"") == '':
			continue

		elif LMCoverageTotal.get(var,"") >= LMRequirementsAll.get(var,""):
			totalCov += LMRequirementsAll.get(var,"")
		
		else:
			totalCov += LMCoverageTotal.get(var,"")

	print "Coverage Percentage : %s" % (float(totalCov) / float(totalReq) * 100)

	Coverage_Percentage = ["Coverage Percentage =",(float(totalCov) / float(totalReq) * 100)]

	CoverageFile = open("CoverageForClusters.csv",'a')
	CoverageFileWriter= csv.writer(CoverageFile,delimiter=',',dialect='excel',lineterminator = '\n')
	CoverageFileWriter.writerow(Coverage_Percentage)
	NumberOfRoutes=["Total Number of Tours:",len(AllRoutes)]
	CoverageFileWriter.writerow(NumberOfRoutes)
	CoverageFile.close()

	CoverReqforLPstr = {}
	for key,value in LMCoverageTotal.items():
		# Put the key in the first column for each key in the dictionary
		CoverReqforLPstr[str(key)] = LMRequirementsAll[key]

	#LP Model & Gurobi Start

	model = gp.Model("mipl")

	CoverReqforLP = dict((k,int(v)) for k,v in CoverReqforLPstr.iteritems())

	route_line_param ={}

	for route_name in Routes:

		for lines in CoverReqforLP.keys():

			if lines in Routes[route_name]:
				route_line_param[route_name,lines]=1
			else:
				route_line_param[route_name,lines]=0

	#Create Decision Variables
	selected_routes = model.addVars(Routes.keys(), lb=0,vtype=GRB.INTEGER,name="open")
	model.update()

	#Objective Function (belki quicksum daha iyi gurobide)
	model.setObjective(sum(CoverReqforLP[j]*150 for j in CoverReqforLP) - sum(1*RouteCosts[i]*selected_routes[i] for i in RouteCosts), GRB.MAXIMIZE)

	#Add Constraints
	for lines in CoverReqforLP:
		model.addConstr(sum(selected_routes[route]*route_line_param[route,lines] for route in Routes.keys())>=CoverReqforLP[lines])

	model.update()
	model.optimize()

	# for v in model.getVars():
	# 	print('%s %g' % (v.varName, v.x))

	Profit=["Profit:",model.objVal]
	ProfitFile = open("CoverageForClusters.csv",'a')
	ProfitFileWriter= csv.writer(ProfitFile,delimiter=',',dialect='excel',lineterminator = '\n')
	ProfitFileWriter.writerow(Profit)
	ProfitFile.close()

	print('Obj: %g' % model.objVal)