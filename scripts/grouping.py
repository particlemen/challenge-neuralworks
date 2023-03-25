import pandas as pd
import numpy as np
from db import DB
import json
import psycopg2

DB_SELECT_QUERY = '''
  SELECT 
  region, origin_latitude, 
  origin_longitude, destination_latitude, 
  destination_longitude, travel_timestamp, 
  datasource, DATE_PART('HOUR', travel_timestamp) as travel_hour
  FROM public.travels
  ORDER BY region, travel_hour;
'''

QUERY_COLUMN_NAMES = [
  "region", "origin_latitude",
  "origin_longitude", "destination_latitude",
  "destination_longitude", "travel_timestamp",
  "datasource", "travel_hour"
]

QUERY_GROUPING_REGION_AND_DATE = """
SELECT region, DATE_PART('WEEK', travel_timestamp) as travel_week,
DATE_PART('YEAR', travel_timestamp) as travel_year, count(1) as num_viajes
FROM public.travels
GROUP BY region, travel_year, travel_week
ORDER BY region;
"""

QUERY_GROUPING_COLUMN_NAMES = [
  "region", "travel_week",
  "travel_year", "num_viajes"
]

CLOSENESS_THRESHOLD = 0.05

def query_sql_a_dataframe(db_cursor):
  try:
    db_cursor.execute(DB_SELECT_QUERY)
  except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error al realizar la query: {error}")
    db_cursor.close()
    return 1
  
  query_results = db_cursor.fetchall()
  db_cursor.close()

  dataframe = pd.DataFrame(query_results, columns= QUERY_COLUMN_NAMES)
  return dataframe

def group_near_travels(dataframe):
  
  close_travels = pd.DataFrame(columns= QUERY_COLUMN_NAMES)
  close_travels_list = []

  for i in range(0,len(dataframe)):
    first_travel = dataframe.iloc[i].to_frame().T
    is_first_travel_not_in_dataframe = True 
    close_travels_to_first_travel = []
    for j in range(i+1, len(dataframe)):
      second_travel = dataframe.iloc[j].to_frame().T
      
      distance_difference_origin_latitude = np.abs(dataframe.iloc[i]["origin_latitude"] - dataframe.iloc[j]["origin_latitude"])
      distance_difference_origin_longitude = np.abs(dataframe.iloc[i]["origin_longitude"] - dataframe.iloc[j]["origin_longitude"])

      distance_difference_destination_latitude = np.abs(dataframe.iloc[i]["destination_latitude"] - dataframe.iloc[j]["destination_latitude"])
      distance_difference_destination_longitude = np.abs(dataframe.iloc[i]["destination_longitude"] - dataframe.iloc[j]["destination_longitude"])

      are_origins_close = np.abs(distance_difference_origin_latitude < CLOSENESS_THRESHOLD) and (distance_difference_origin_longitude < CLOSENESS_THRESHOLD)
      are_destinations_close = np.abs(distance_difference_destination_latitude < CLOSENESS_THRESHOLD) and (distance_difference_destination_longitude < CLOSENESS_THRESHOLD)

      if (are_origins_close and are_destinations_close):
        
        if is_first_travel_not_in_dataframe:
          close_travels_to_first_travel = [first_travel.values.tolist()]
          close_travels_to_first_travel[-1][-1][5] = close_travels_to_first_travel[-1][-1][5]._repr_base
          is_first_travel_not_in_dataframe = False

        close_travels_to_first_travel.append(second_travel.values.tolist())
        close_travels_to_first_travel[-1][-1][5] = close_travels_to_first_travel[-1][-1][5]._repr_base
    
    if len(close_travels_to_first_travel) > 0:
      close_travels_list.append(close_travels_to_first_travel)

  return close_travels_list

def get_similar_travels(travel_dataframe):
  
  close_travels = []

  travel_regions = pd.unique(travel_dataframe['region'])

  for region in travel_regions:

    travels_in_region = travel_dataframe[ travel_dataframe['region'] == region ]
    unique_travel_hours = pd.unique(travels_in_region['travel_hour'])
    
    for travel_hour in unique_travel_hours:

      travels_same_region_same_hour = travels_in_region[ travels_in_region['travel_hour'] == travel_hour ]

      if len(travels_same_region_same_hour) > 1:

        close_travel_group = group_near_travels(travels_same_region_same_hour)
        
        if len(close_travel_group) > 0:
          close_travels.append(close_travel_group)
    
  return close_travels


if __name__ == "__main__":
  db_connection = DB()
  travels_dataframe = query_sql_a_dataframe(db_connection.get_cursor())
  print(json.dumps(get_similar_travels(travels_dataframe)))