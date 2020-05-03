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
import numpy as np

from BU2019_CentralParameters import *
from BU2019_BasicFunctionsLib import *
from BU2019_TourSearch import *
from BU2020_AssignmentFunctions import *

dbcon = psycopg2.connect(**PrimaryDB) 
dbcur = dbcon.cursor()
RelevantLineCategories = ['RE','R','IR','IC','ICE','S']
RelevantManagements = [11,33]

RouteConditions1 = {
	# von und bis Haltestelle (mandatory condition)
	Cond.StartAndEndStations: (8503000, 8503000), 	
	
	# StartTime in Hour und Minute, MinDuration, MaxDuration in minutes (mandatory condition)
	# determines earliest and latest arrival to end station
	Cond.StartTimeAndDuration: (8, 0, 60, 120),		
	
	# Max Wartezeit bei einer Haltestelle in Minuten (mandatory condition)
	Cond.MaxWaitingTimeAtStation: (30,),			
	
	
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
	Cond.MaxSearchTimeInSeconds: (40,),
	}

(TimeTableList, TimeTableIndex, StationHourIndex) = ReadTimeTable(dbcur, RouteConditions1)

arr=np.array(TimeTableList)
DistinctLineID=np.unique(arr[:,ConnInfoInd['line_id']])
DistinctLineID = [x for x in DistinctLineID if x is not None and x is not '-1']

StationListForLines=dict() #Dictionary Containing Stations that Lines Operate

for line in DistinctLineID:

	StationList=set()

	for connection in arr:

		if connection[ConnInfoInd['line_id']]==line:
			StationList.add(connection[ConnInfoInd['station_from']])
			StationList.add(connection[ConnInfoInd['station_to']])

	StationListForLines[line] = StationList

#PrintDictionaryContent(StationListForLines)

def common_member(a, b): 
    if (a & b): 
        return True 
    else: 
        return False

def Intersection(StationListForLines):
	
	Proximity1=dict()
	
	for index1, (key1, value1) in enumerate(StationListForLines.items()):
		Proximity=set()
		for index2, (key2, value2) in enumerate(StationListForLines.items()):

			if common_member(value1, value2) and key1!=key2:

				Proximity.add(key2)
			
		Proximity1[key1]=Proximity
	
	return Proximity1

Proximity1= Intersection(StationListForLines) # Dictionary Containing Intersecting Lines

Proximity2=dict() #Dictionary Containing Lines and Their Neighbor Lines Reachable with 2 transfers

for index1, (key1, value1) in enumerate(Proximity1.items()):

	Proximity=set()

	for index2, (key2, value2) in enumerate(Proximity1.items()):
		
		if key2 in value1:

			Proximity=Proximity.union(value2)
	
	Proximity2[key1]=Proximity

# print "1Proximity" 
# print Proximity1
# print "2Proximity" 
# print Proximity2

StartStation=RouteConditions1[Cond.StartAndEndStations][0]

PossibleStartingLines = [ k for k in StationListForLines.keys() if StartStation in StationListForLines[k] ]

ReachableLines2=[Proximity2.get(key) for key in PossibleStartingLines]
ReachableLines1=[Proximity1.get(key) for key in PossibleStartingLines]

ReachableLines = set().union(*ReachableLines2) 
ReachableLines =ReachableLines.union(*ReachableLines1) #Reachable Lines with at most 2 transfers starting from specified station 

print ReachableLines