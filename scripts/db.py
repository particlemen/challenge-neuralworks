import csv
import sys
import psycopg2

CREATE_TABLE_SCRIPT = '''
  CREATE TABLE IF NOT EXISTS travels (
    region VARCHAR(50),
    origin_latitude REAL,
    origin_longitude REAL,
    destination_latitude REAL,
    destination_longitude REAL,
    travel_timestamp TIMESTAMP,
    datasource VARCHAR(50),
    upload_timestamp TIMESTAMP
  );
'''

DB_SELECT_QUERY = '''
  SELECT 
  region, origin_latitude, 
  origin_longitude, destination_latitude, 
  destination_longitude, travel_timestamp, 
  datasource
  FROM public.travels;
'''

INSERT_VALUE_SCRIPT = '''
  INSERT INTO travels (region, 
    origin_latitude, 
    origin_longitude,
    destination_latitude,
    destination_longitude,
    travel_timestamp,
    datasource,
    upload_timestamp
  ) 
  VALUES (
    %s, %s, %s, %s, %s, %s, %s, NOW()
  );
'''

DB_NAME = "neuralworks"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432

class DB:
  def __init__(self):
    print("Conectandose a la base de datos.")
    self.db_connection = psycopg2.connect(
      dbname=DB_NAME, 
      user=DB_USER, 
      password=DB_PASS,
      host = DB_HOST,
      port = DB_PORT
    )
    print("Conexion exitosa.")
    self.create_initial_table()

  def __del__(self):
    self.db_connection.close()
    
  def create_initial_table(self):
    
    db_cursor = self.get_cursor()
    print(f"Creando tabla travels en la base de datos {DB_NAME} si no existe.")
    db_cursor.execute(CREATE_TABLE_SCRIPT)
    self.commit_changes()

    db_cursor.close()
    return

  def commit_changes(self):
    self.db_connection.commit()

  def get_cursor(self):
    return self.db_connection.cursor()

def load_csv_file_to_db(file_path, db_cursor):
  
  with open(file_path, newline="\n") as csv_file:
    destinations_csv = csv.reader(csv_file)
    next(destinations_csv)
    print("Comenzando carga de datos desde el csv.")
    for line in destinations_csv:
      origin_coordinates = line[1].split(' ')[1:]
      destination_coordinates = line[2].split(' ')[1:]
      try:
        db_cursor.execute( INSERT_VALUE_SCRIPT,
          (
            line[0],
            float(origin_coordinates[0][1:]),
            float(origin_coordinates[1][:-1]),
            float(destination_coordinates[0][1:]),
            float(destination_coordinates[1][:-1]),
            line[3],
            line[4]
          )
        )
      except (psycopg2.DatabaseError) as error:
        print("Error al agregar la fila a la base de datos")
        print(line)
        print("-"*40)

    db_cursor.close()
  
  return

if __name__ == "__main__":
  csv_path = sys.argv[1]
  db_connection = DB()
  load_csv_file_to_db(csv_path, db_connection.get_cursor())
  db_connection.commit_changes()
  del db_connection

  print(f"Completada la carga de datos desde el archivo {csv_path}.")