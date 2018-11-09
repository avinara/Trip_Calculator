import pandas as pd
import datetime as dt
from geopy.distance import vincenty

import conf


def calcDistance(df, idx):
    return vincenty( (df['latitude'][idx],   df['longitude'][idx]),
                     (df['latitude'][idx-1], df['longitude'][idx-1]) ).meters

def generateTripPoint(df, sIndex, eIndex, totDist):
    # Vehicle ID
    busId = df['vehicle_id'][sIndex]

    # Grid generation
    grid = [0] * conf.GRID_FEATURES

    prevGrid = df['grid_no'][sIndex]

    for r in range(sIndex + 1, eIndex):
        currGrid = df['grid_no'][r]
        if currGrid == prevGrid: grid[int(currGrid)] += calcDistance(df, r)
        prevGrid = currGrid
    
    # Timestamp calculation
    startTime = dt.datetime.strptime(df['timestamp'][sIndex] , '%Y-%m-%d %H:%M:%S').timestamp()
    endTime = dt.datetime.strptime(df['timestamp'][eIndex] , '%Y-%m-%d %H:%M:%S').timestamp()

    travelTime = endTime - startTime

    # Average speed
    avgSpeed = totDist / travelTime

    # co-ordinates
    ordinates = [ df['latitude'][sIndex], df['longitude'][sIndex],
                  df['latitude'][eIndex], df['longitude'][eIndex] ]

    dataPoint = [busId, df['timestamp'][sIndex], totDist]
    dataPoint.extend(ordinates)
    dataPoint.extend(grid)
    dataPoint.extend([avgSpeed, travelTime])
    print(dataPoint)
    return (tuple(dataPoint))
       
def slidingWindow(df, busId, index):
    dfRows = len(df.index)
    nextBusId = df['vehicle_id'][index + conf.WINDOW_SIZE]

#    if (index + conf.WINDOW_SIZE > dfRows) or (busId != nextBusId):
#        return False

    lSwDist = [calcDistance(df, i + index) for i in range(1, conf.WINDOW_SIZE)]

    return lSwDist

def goToNextVehicle(df, index):
    dfRows = len(df.index)
    currId = df['vehicle_id'][index]

    while df['vehicle_id'][index] != currId and index < dfRows:
        index += 1

    return index
    
def parseRecords(df):
    # Initialize
    currIndex = 0
    dfRows = len(df.index)

    dataTuples = []

    while (currIndex < dfRows):
        # Current Bus Id
        busId = df['vehicle_id'][currIndex]
        tripStartIndex = -1; tripStarted = False
        
        lSwDist = slidingWindow(df, busId, currIndex)

        if lSwDist == False:
            currIndex = goToNextVehicle(df, currIndex)
            continue

        swDist = totDist = sum(lSwDist)
        currIndex += conf.WINDOW_SIZE
        currBusId = df['vehicle_id'][currIndex]

        busStatus = (swDist > conf.DISTANCE_THRESHOLD)
        if (busStatus):
            tripStartIndex = currIndex - conf.WINDOW_SIZE
            tripStarted = True

        while (currBusId == busId) and (currIndex < dfRows):
            currBusId = df['vehicle_id'][currIndex]
            currDist = calcDistance(df, currIndex)

            swDist += currDist - lSwDist.pop(0)
            lSwDist.append(currDist)

            busStatus = (swDist > conf.DISTANCE_THRESHOLD)

            if tripStarted:
                totDist += currDist
                tripStarted = busStatus

                # Trip ended!
                if not busStatus and (totDist > conf.TRIP_DISTANCE):
                    # Yay! Valid trip
                    tripStopIndex = currIndex-1
                    dataTuples.append( generateTripPoint(df, tripStartIndex, tripStopIndex, totDist) )

                    lSwDist = slidingWindow(df, busId, currIndex)

                    if lSwDist == False:
                        currIndex = goToNextVehicle(df, currIndex)
                    else:
                        currIndex += conf.WINDOW_SIZE
                        swDist = totDist = sum(lSwDist)

                    continue

            # New Trip
            elif busStatus:
                tripStartIndex = currIndex - conf.WINDOW_SIZE
                totDist = swDist
                tripStarted = True

            currIndex += 1

        if tripStarted and (totDist > conf.TRIP_DISTANCE):
            tripStopIndex = currIndex-1; tripStarted = False
            dataTuples.append( generateTripPoint(df, tripStartIndex, tripStopIndex, totDist) )

    return dataTuples

def calculate(inputCsv):
    df = pd.read_csv(inputCsv, index_col=0)
    dt = parseRecords(df)

    col = ["vehicle_id", "start_time", "total_dist", "start_lat", "start_long", "end_lat", "end_long"]
    col.extend( [str(x) for x in range(0,conf.GRID_FEATURES)] )
    col.extend(["avg_speed", "travel_time"])

    datapoint = pd.DataFrame(dt, columns=col)

    datapoint.to_csv("./res/out.csv")

    
    
