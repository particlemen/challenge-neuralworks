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

#Parametros para la conexion a la base de datos
DB_NAME = "neuralworks"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "db"
DB_PORT = 5432

class DB:
  """
  Clase que encapsula todas la conexion a la base de datos.
  """
  def __init__(self):
    """
    Al crear la clase se realiza la conexion a las base de datos.
    """
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
    """
    Al momento de borrar la clase DB, se realiza una desconexion a la base de datos.
    """
    self.db_connection.close()
    
  def create_initial_table(self):
    """
    Se crea la tabla travels en la base de datos si es que esta no existe
    Siempre se ejecuta este metodo al iniciar la conexion a la base de datos
    """
    db_cursor = self.get_cursor()
    print(f"Creando tabla travels en la base de datos {DB_NAME} si no existe.")
    db_cursor.execute(CREATE_TABLE_SCRIPT)
    self.commit_changes()

    db_cursor.close()
    return

  def commit_changes(self):
    """
    Se realiza un commit de los cambios en la base de datos
    """
    self.db_connection.commit()

  def get_cursor(self):
    """
    Se obtiene un cursor de la base de datos para usarla en queries
    """
    return self.db_connection.cursor()

def load_csv_file_to_db(file_path, db_cursor):
  """
  Carga el csv indicado en file_path y realiza la carga de este en la base de datos
  mediante el uso del cursor db_cursor
  """
  with open(file_path, newline="\n") as csv_file:
    destinations_csv = csv.reader(csv_file)
    next(destinations_csv) #Salto los headers
    print("Comenzando carga de datos desde el csv.")
    for line in destinations_csv: #Itero por las lineas del csv
      #Separo los valores de las coordenadas desde Point(x y) a una lista de dos valores separados por el espacio 
      origin_coordinates = line[1].split(' ')[1:] 
      destination_coordinates = line[2].split(' ')[1:]
      try:
        #Realizo la query para insertar los valores
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

    #cierro el cursor
    db_cursor.close()
  
  return

if __name__ == "__main__":
  #Obtengo el path desde los argumentos de la terminal
  csv_path = sys.argv[1]
  #Creo una conexion a la base de datos
  db_connection = DB()
  #Cargo el CSV
  load_csv_file_to_db(csv_path, db_connection.get_cursor())
  #Hago un commit de los cambios
  db_connection.commit_changes()
  #Cierro la conexion a la base de datos
  del db_connection

  print(f"Completada la carga de datos desde el archivo {csv_path}.")