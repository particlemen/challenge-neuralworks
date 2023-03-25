from fastapi import FastAPI 
from scripts.db import DB
import psycopg2

app = FastAPI()

SELECT_QUERY_BOUNDING_AND_REGION = """
SELECT region, DATE_PART('WEEK', travel_timestamp) as travel_week,
DATE_PART('YEAR', travel_timestamp) as travel_year, count(1) as num_viajes
FROM public.travels
WHERE (origin_latitude BETWEEN %s AND %s) AND (origin_longitude BETWEEN %s AND %s) 
AND (destination_latitude BETWEEN %s AND %s) AND (destination_longitude BETWEEN %s AND %s)
AND lower(region) = %s 
GROUP BY region, travel_year, travel_week
ORDER BY region;
""" 

SELECT_QUERY_STATE_OF_INGEST = """
SELECT count(1), upload_timestamp
FROM public.travels 
GROUP BY upload_timestamp;
"""

db_connection = DB()

def process_weekly_resume(weekly_resume_list, region):

  weekly_resume = {}
  weekly_resume["region"] = region
  weekly_resume["travels"] = []

  years = {}

  i = 0

  for week in weekly_resume_list:
    (region, week, year, travel_quantity) = week
    if year not in years:
      years[year] = i
      i+=1
      weekly_resume["travels"].append([])
      weekly_resume["travels"][years[year]] = {"year": int(year)}
      weekly_resume["travels"][years[year]]["travels"] = []
      

    weekly_resume["travels"][years[year]]["travels"].append({"week_of_year": int(week), "travel_quantity": travel_quantity})

  return weekly_resume

def calculate_upload_statistics(upload_results):
  last_update = upload_results[0]
  total_records = sum([day[0] for day in upload_results])
  return {
    "last_uploaded_day": last_update[1],
    "records_uploaded_on_last_day": last_update[0],
    "total_records": total_records
  }

@app.get("/")
async def read_root():
  return {"Hola": "Neuralworks"}

@app.get("/weekly_travel_resume/{region}")
async def get_weekly_resume(region, min_latitude = 0,  max_latitude=180, min_longitude=0, max_longitude=180):
  db_cursor = db_connection.get_cursor()
  try:
    db_cursor.execute(SELECT_QUERY_BOUNDING_AND_REGION, (
      min_latitude, max_latitude, min_longitude, max_longitude,
      min_latitude, max_latitude, min_longitude, max_longitude, region.lower()))
  except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error al realizar la query: {error}")
    db_cursor.close()
    return 1
  
  query_results = db_cursor.fetchall()
  db_cursor.close()

  return process_weekly_resume(query_results, region.capitalize())

@app.get("/data_ingest_state")
async def get_data_ingest_state():
  db_cursor = db_connection.get_cursor()
  try:
    db_cursor.execute(SELECT_QUERY_STATE_OF_INGEST)
  except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error al realizar la query: {error}")
    db_cursor.close()
    return 1
  
  query_results = db_cursor.fetchall()
  db_cursor.close()

  return calculate_upload_statistics(query_results)