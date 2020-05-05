
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

trial=set()
trial=trial.union(StationListForLines['6.S10'])
trial=trial.union(StationListForLines['4.S6b'])
trial=trial.union(StationListForLines['7.S5a'])

DistinctStations=np.unique(arr[:,ConnInfoInd['station_from']])
b=np.unique(arr[:,ConnInfoInd['station_to']])
DistinctStations=set(DistinctStations)
b=set(b)
DistinctStations.update(b)
#print DistinctStations


#Setting the connection score to "0" for Required Lines' connections
for connection_row in TimeTableList:

	if connection_row[ConnInfoInd['line_id']] in list(list(zip(*LMRequirementsAll)[0])):
		ind=TimeTableList.index(connection_row) #converting to list for changing connection score
		connection_row=list(connection_row)
		connection_row[ConnInfoInd['connection_score']]=0
		connection_row=tuple(connection_row) #converting back to tuple
		TimeTableList[ind]=connection_row #changing the TimeTableList

CoveredStations=set()

def ConnectionScoring(StationList,level):
	#StationList: Stations of lines which we want to cover (trial is used as an example)
	#level= neighborhood level of all other connections
	
	global CoveredStations #Set of so far Covered stations 
	global TimeTableList

	if CoveredStations == DistinctStations:
		return #Returns final(with final connection scores) TimeTableList

	if len(CoveredStations) is 0:
		CoveredStations=CoveredStations.union(StationList) 
	else:
		CoveredStations.update(StationList)
	Intersection=set()
	for station in StationList:

		for connection_row in TimeTableList:
			
			if connection_row[ConnInfoInd['station_from']]==station:
				ind=TimeTableList.index(connection_row) 
				connection_row=list(connection_row) #converting to list for changing connection score
				if connection_row[ConnInfoInd['station_to']] not in CoveredStations:
					Intersection.add(connection_row[ConnInfoInd['station_to']])

				if ((connection_row[ConnInfoInd['connection_score']]==None) or (connection_row[ConnInfoInd['connection_score']]>level)):
					connection_row[ConnInfoInd['connection_score']]=level
				connection_row=tuple(connection_row) #converting back to tuple
				TimeTableList[ind]=connection_row #changing the TimeTableList
				
	level=level+1
	if level ==15:
		print "sadas"
	ConnectionScoring(Intersection,level)

# ConnectionScoring(trial,1)

# print "asdsa"

# for rows in TimeTableList:
# 	if rows[ConnInfoInd['connection_score']]==0:
# 		print rows


# print "asdasd"