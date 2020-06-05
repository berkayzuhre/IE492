import numpy as np
import pandas as pd
import time
import timeit
import math

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

StationCoordinates=pd.read_excel("coordinates_egecan.xlsx",index_col=0)

#print StationCoordinates.at[8505216,'x']

StationDistance=pd.DataFrame(np.full((len(StationCoordinates.index),len(StationCoordinates.index)),None),columns=StationCoordinates.index)
StationDistance['station']=StationCoordinates.index
StationDistance=StationDistance.set_index('station',drop=True)

for station1 in StationCoordinates.index:

	for station2 in StationCoordinates.index:

		StationDistance.at[station1,station2]=math.sqrt(((StationCoordinates.at[station1,'x']-StationCoordinates.at[station2,'x'])**2)+((StationCoordinates.at[station1,'y']-StationCoordinates.at[station2,'y'])**2))

print StationDistance


# RequirementsSet=set(list(list(zip(*LMRequirementsAll)[0])))
# StationListForLines=pd.read_excel("StationListForLines.xlsx",index_col=0,header=None)

# #Initializing connection scoring dataframe with respect to requirements
# RequirementScores = pd.DataFrame(np.full((len(TimeTableList),len(RequirementsSet)),None),columns=RequirementsSet)
# RequirementScores['conn_id']=conn_id
# RequirementScores=RequirementScores.set_index('conn_id',drop=True)

# #Filling out the Requirements Score dataframe 
# for requirement in RequirementsSet:
#     start_time2 = timeit.default_timer()
#     Stations=StationListForLines[requirement]
#     Stations=list(Stations)

#     #Setting the earliest arrival to "0" for requirement line's stations
#     #EarliestArrival.loc[:,Stations]=0

#     #Setting the connection score to "0" for requirement line's connections
#     for connection_row in TimeTableList:
#         if connection_row[ConnInfoInd['line_id']] == requirement:
#             RequirementScores.at[connection_row[ConnInfoInd['conn_id']],requirement]=0
#         else:
#             RequirementScores.at[connection_row[ConnInfoInd['conn_id']],requirement]=EarliestArrival.loc[connection_row[ConnInfoInd['station_to']],Stations].mean()+connection_row[ConnInfoInd['arrival_totalmin']]-connection_row[ConnInfoInd['departure_totalmin']]
#     elapsed2 = timeit.default_timer() - start_time2
#     print 'line %s reqscore takes %f ' %(requirement,elapsed2)

# elapsed1 = timeit.default_timer() - start_time1
# print 'initial reqscore takes %f ' %(elapsed1)

# RequirementScores.to_excel("reqscores.xlsx")