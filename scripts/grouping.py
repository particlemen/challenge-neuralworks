import pandas as pd
import numpy as np
from db import DB
import json
import psycopg2

#Query para hacer un select de los elementos de la base de datos
DB_SELECT_QUERY = '''
  SELECT 
  region, origin_latitude, 
  origin_longitude, destination_latitude, 
  destination_longitude, travel_timestamp, 
  datasource, DATE_PART('HOUR', travel_timestamp) as travel_hour
  FROM public.travels
  ORDER BY region, travel_hour;
'''

#Nombres de las columnas del dataframe
QUERY_COLUMN_NAMES = [
  "region", "origin_latitude",
  "origin_longitude", "destination_latitude",
  "destination_longitude", "travel_timestamp",
  "datasource", "travel_hour"
]

#Query usada para hacer un grouping de los viajes por region, año y semana del año
QUERY_GROUPING_REGION_AND_DATE = """
SELECT region, DATE_PART('WEEK', travel_timestamp) as travel_week,
DATE_PART('YEAR', travel_timestamp) as travel_year, count(1) as num_viajes
FROM public.travels
GROUP BY region, travel_year, travel_week
ORDER BY region;
"""

#Nombres de las columnas usadas en el dataframe de las queries de los grouping
QUERY_GROUPING_COLUMN_NAMES = [
  "region", "travel_week",
  "travel_year", "num_viajes"
]

#Limite de diferencia de distancia de grados de latitud y longitud para decir que dos viajes son iguales
CLOSENESS_THRESHOLD = 0.05

def query_sql_a_dataframe(db_cursor):
  """
  Realizo la query para obtener todos los viajes realizados desde la base de datos
  y los pasa a un dataframe de pandas
  """
  try:
    #Ejecuto la query en la base de datos
    db_cursor.execute(DB_SELECT_QUERY)
  except (Exception, psycopg2.DatabaseError) as error:
    print(f"Error al realizar la query: {error}")
    db_cursor.close()
    return 1
  
  #Obtengo todos los resultados
  query_results = db_cursor.fetchall()
  #Cierro el cursor
  db_cursor.close()

  #Creo el dataframe y lo retorno
  dataframe = pd.DataFrame(query_results, columns= QUERY_COLUMN_NAMES)
  return dataframe

def group_near_travels(dataframe):
  """
  Acepta un sub-dataframe con viajes que comparten la hora del dia y la region
  Retorna una lista de los viajes y los que que tiene un origen y destino cercano a este.
  Para obtener la cercania, se restan las latitudes y longitudes, al comparar que la diferencia sea menor
  al limite definido en CLOSENESS_THRESHOLD, se asume que estos son cercanos.
  """

  #Lista de los viajes cercanos
  close_travels_list = []

  #Itero por los viajes
  for i in range(0,len(dataframe)):
    #Obtengo el viaje actual en la lista
    first_travel = dataframe.iloc[i].to_frame().T
    #Lo inicializo como que no esta en la lista de close_travels_list
    is_first_travel_not_in_travel_list = True 
    #Lista de los viajes cercanos al actual
    close_travels_to_first_travel = []
    #Itero desde el viaje actual, ya que si un viaje A es cercano a B, B tambien es cercano a A
    for j in range(i+1, len(dataframe)):
      #Viaje a comparar con el primero
      second_travel = dataframe.iloc[j].to_frame().T
      
      #Obtengo las diferencias de las latitudes y longitudes de origen del viaje
      distance_difference_origin_latitude = np.abs(dataframe.iloc[i]["origin_latitude"] - dataframe.iloc[j]["origin_latitude"])
      distance_difference_origin_longitude = np.abs(dataframe.iloc[i]["origin_longitude"] - dataframe.iloc[j]["origin_longitude"])

      #Obtengo las diferencias de las latitudes y longitudes del destino del viaje
      distance_difference_destination_latitude = np.abs(dataframe.iloc[i]["destination_latitude"] - dataframe.iloc[j]["destination_latitude"])
      distance_difference_destination_longitude = np.abs(dataframe.iloc[i]["destination_longitude"] - dataframe.iloc[j]["destination_longitude"])

      #Veo si estas diferencias cumplen con el limite
      are_origins_close = np.abs(distance_difference_origin_latitude < CLOSENESS_THRESHOLD) and (distance_difference_origin_longitude < CLOSENESS_THRESHOLD)
      are_destinations_close = np.abs(distance_difference_destination_latitude < CLOSENESS_THRESHOLD) and (distance_difference_destination_longitude < CLOSENESS_THRESHOLD)

      if (are_origins_close and are_destinations_close):
        
        if is_first_travel_not_in_travel_list:
          #Creo una lista con los viajes cercanos al primero
          close_travels_to_first_travel = first_travel.values.tolist()
          #Obtengo la representacion base en string del timestamp
          close_travels_to_first_travel[-1][5] = close_travels_to_first_travel[-1][5]._repr_base
          is_first_travel_not_in_travel_list = False

        #Añado el viaje cercano a la lista de los viajes
        close_travels_to_first_travel.append(second_travel.values.tolist()[0])
        close_travels_to_first_travel[-1][5] = close_travels_to_first_travel[-1][5]._repr_base
    
    if len(close_travels_to_first_travel) > 0:
      close_travels_list.append(close_travels_to_first_travel)

  #Retorno los viajes cercanos
  return close_travels_list

def get_similar_travels(travel_dataframe):
  """
  Obtengo el data frame y realizo las comparaciones con viajes con la misma region y hora del dia
  """

  #Lista de los viajes cercanos
  close_travels = []

  #Obtengo las regiones unicas del dataframe
  travel_regions = pd.unique(travel_dataframe['region'])

  #Itero por las regiones
  for region in travel_regions:

    #Subdataframe con los viajes dentro de la misma region
    travels_in_region = travel_dataframe[ travel_dataframe['region'] == region ]
    #Dentro de este subdataframe obtengo las horas unicas de los viajes
    unique_travel_hours = pd.unique(travels_in_region['travel_hour'])
    
    #Itero por las horas unicas de los viajes
    for travel_hour in unique_travel_hours:

      #Subdataframe con los viajes dentro de una region a la misma hora del dia
      travels_same_region_same_hour = travels_in_region[ travels_in_region['travel_hour'] == travel_hour ]

      #Si hay mas de un viaje con este filtro, se hace la cimparacion
      if len(travels_same_region_same_hour) > 1:

        #Realizo la comparacion de los viajes
        close_travel_group = group_near_travels(travels_same_region_same_hour)
        
        #Si hay viajes cercanos, los añado
        if len(close_travel_group) > 0:
          close_travels.append(close_travel_group)
    
  return close_travels

if __name__ == "__main__":
  #Creo la conexion a la base de datos
  db_connection = DB()
  #Obtengo el dataframe de la consulta SQL
  travels_dataframe = query_sql_a_dataframe(db_connection.get_cursor())
  #Lo transformo a JSON y lo imprimo
  print(json.dumps(get_similar_travels(travels_dataframe)))