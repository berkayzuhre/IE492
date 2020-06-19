#!/usr/bin/env python
#-*- coding: utf-8 -*-
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
import timeit
from datetime import date 
from datetime import datetime
from datetime import timedelta
from openpyxl import Workbook
import calendar
import itertools as it
from collections import OrderedDict 

import csv
from matplotlib import pyplot as plt
import gurobipy as gp
from gurobipy import GRB
from pandas import *
import numpy as np

from GlobalVariables import*
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
# 8507000: Bern ->1.R3
# 8503000: Zürich
# 8501008: Geneva -> 6.S41
# 8500010: Basel -> 1.R3
#1.R3 & 6.S41 & 7.S24a

# conditions for tour search
# Bern --> Zürich
RouteConditions1_30_300 = {
	# von und bis Haltestelle (mandatory condition)
	Cond.StartAndEndStations: (8507000, 8507000), 	
	
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
	Cond.MaxSearchTimeInSeconds: (159744,),

	Cond.ReturnFromCurrentStation: True,

	Cond.VisitAStationOnlyOnce: True,

	}

# **************************************************************************************

# def TEST_ReadTimeTable():

# 	(TimeTableList, TimeTableIndex, StationHourIndex) = ReadTimeTable(dbcur, RouteConditions1)
# 	print "TimeTableList:"
# 	for line in TimeTableList:
# 		print line

def TEST_FindAndDisplayRoutes(Requirements,ClusterIndex,EarliestArrival,RouteConditions):
	"""
	if Read_RouteInfoList_FromFile = True AND a saved variable exists --> read tours from saved variable
	Otherwise, search tours and save results (i.e. list of tours, RouteInfoList1)
	"""
	global RouteInfoList1
	print "\nFind all routes for the given route conditions..."

	if not Read_RouteInfoList_FromFile or not RouteInfoList1:
		print "\nFind routes for the given route conditions..."
		(RouteInfoList1, StatusReport, TerminationReasons) = FindAllRoutes(dbcur, RouteConditions,Requirements,EarliestArrival,ClusterIndex)
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

	# N = 10

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

	#TEST_FindAndDisplayRoutes(requirement_clusters[2],2,EarliestArrival,RouteConditions1_30_300)

	# cw = open("covered.csv",'wb')
	# Writer= csv.writer(cw,delimiter=',', dialect='excel')
	# Writer.writerow(list(CoveredStations))
	# cw.close()

	for i in range(10):
		print LineSeparator
		print "CLUSTER"+str(i)
		
		#Finding Appropriate Starting Station
		
		StartingStation=BestStartingStation(requirement_clusters[i],StationListForLines,EarliestArrival)
		print "Starting station for Cluster %d is %d" %(i,StartingStation)
		RequirementsSet=set(list(list(zip(*requirement_clusters[i])[0])))
		RequirementsSet=list(RequirementsSet)

		TotalSearchTimInSeconds=7200
		SearchTime=len(RequirementsSet)*(TotalSearchTimInSeconds)/len(RequirementScores.columns.values)
		
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

				Cond.ReturnFromCurrentStation: True,

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

				Cond.ReturnFromCurrentStation: True,

				Cond.VisitAStationOnlyOnce: True,

				}
		FoundRoutes=TEST_FindAndDisplayRoutes(requirement_clusters[i],i,EarliestArrival,RouteConditions)
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

	#AllRoutes = list(OrderedDict.fromkeys(AllRoutes))

	print LineSeparator
	print "Evaluate tours"
	print LineSeparator

	print "AllRoutes is a list that contains %s routes." % len(AllRoutes)

	# **************************************************************************************
	# Line Measurement (LM) Coverage of Routes
	# **************************************************************************************
	print LineSeparator 
	print "Line Measurement (LM) Coverage of Routes"
	print LineSeparator

	# In order to calculate the Line Measurement (LM) coverage of a route,
	# we need to have first LMRequirementsAll per LineKey (LineID, TimeWindow, WeekdayGroup):

	LMCoverageTotal = {}
	RouteDuration={}
	RouteInd=1
	CoverPerRouteResults=[]

	for RouteInfo in AllRoutes:
		RouteName='Route' + str(RouteInd)
		(LMCoveragePerSegment, LMCoveragePerLineKey) = \
			GetLMCoverageOfRoute(RouteInfo, ReqLineMeasureTime, PeriodBegin, PeriodEnd, LMRequirements=LMRequirementsAll)
		
		if len(LMCoveragePerLineKey)>0:

			RouteInd = RouteInd+1
			for key,value in LMCoveragePerLineKey.items():
				# Put the key in the first column for each key in the dictionary
				csv_row=[]
				csv_row.append(RouteName)
				csv_row.append(str(key))
				csv_row.append(value)
				CoverPerRouteResults.append(csv_row)
			departure_first_station = RouteInfo[0][ConnInfoInd['departure_hour']]*60 + RouteInfo[0][ConnInfoInd['departure_min']]
			arrival_last_station = RouteInfo[-1][ConnInfoInd['arrival_hour']]*60 + RouteInfo[-1][ConnInfoInd['arrival_min']]
			routeDur=arrival_last_station-departure_first_station
			RouteDuration[RouteName]=routeDur

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
			totalCov += LMRequirementsAll.get(var,"")

	print "Coverage Percentage : %s" % (float(totalCov) / float(totalReq) * 100)

	Coverage_Percentage = ["Coverage Percentage =",(float(totalCov) / float(totalReq) * 100)]

	CoverageFile = open("CoverageForClusters.csv",'a')
	CoverageFileWriter= csv.writer(CoverageFile,delimiter=',',dialect='excel',lineterminator = '\n')
	CoverageFileWriter.writerow(Coverage_Percentage)
	NumberOfRoutes=["Total Number of Tours:",len(AllRoutes)]
	CoverageFileWriter.writerow(NumberOfRoutes)
	CoverageFile.close()

	CoverPerRouteResultFile = open("CoverPerRoute.csv",'wb')
	CoverPerRouteResultFileWriter= csv.writer(CoverPerRouteResultFile,delimiter=',', dialect='excel')
	CoverPerRouteResultFileWriter.writerows(CoverPerRouteResults)
	CoverPerRouteResultFile.close()

	RouteDurationResults=[]

	for key,value in RouteDuration.items():
		# Put the key in the first column for each key in the dictionary
		csv_row=[]
		csv_row.append(str(key))
		csv_row.append(value)
		RouteDurationResults.append(csv_row)
	
	RouteDurationResultsFile = open("RouteDuration.csv",'wb')
	RouteDurationResultsFileWriter= csv.writer(RouteDurationResultsFile,delimiter=',', dialect='excel')
	RouteDurationResultsFileWriter.writerows(RouteDurationResults)
	RouteDurationResultsFile.close()

	CoverReqForLPResults=[]

	for key,value in LMCoverageTotal.items():
		# Put the key in the first column for each key in the dictionary
		csv_row=[]
		csv_row.append(str(key))
		csv_row.append(LMRequirementsAll[key])
		CoverReqForLPResults.append(csv_row)
	
	CoverReqForLPResultsFile = open("CoverReqforLP.csv",'wb')
	CoverReqForLPResultsFileWriter= csv.writer(CoverReqForLPResultsFile,delimiter=',', dialect='excel')
	CoverReqForLPResultsFileWriter.writerows(CoverReqForLPResults)
	CoverReqForLPResultsFile.close()

	#LP Model Start

	reader1 = csv.reader(open('RouteDuration.csv', 'r'))
	RouteCosts = {}
	for row in reader1:
		k, v = row
		RouteCosts[k] = v

	reader2 = csv.reader(open('CoverReqforLP.csv', 'r'))
	CoverReqforLPstr = {}
	for row in reader2:
		k, v = row
		CoverReqforLPstr[k] = v

	reader3= csv.reader(open('CoverPerRoute.csv', 'r'))
	Route_Number = []
	Reqs = []
	Values = []
	
	for row in reader3:
		k, v, l = row
		Route_Number.append(k)
		Reqs.append(v)
		Values.append(l)

	Routes = {}

	for i in range(len(Route_Number)):

		if Route_Number[i] not in Routes : 
			Routes[Route_Number[i]]={}

		Routes[Route_Number[i]][Reqs[i]]=Values[i]

	#Gurobi Start

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
