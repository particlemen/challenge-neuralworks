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
    datasource VARCHAR(50)
  );
'''

INSERT_VALUE_SCRIPT = '''
  INSERT INTO travels (region, 
    origin_latitude, 
    origin_longitude,
    destination_latitude,
    destination_longitude,
    travel_timestamp,
    datasource
  ) 
  VALUES (
    %s, %s, %s, %s, %s, %s, %s
  );
'''

DB_NAME = "neuralworks"
DB_USER = "postgres"
DB_PASS = "postgres"
DB_HOST = "localhost"
DB_PORT = 5432

def load_csv_file_to_db(file_path, db_cursor):
  with open(file_path, newline="\n") as csv_file:
    destinations_csv = csv.reader(csv_file)
    next(destinations_csv)
    for line in destinations_csv:
      origin_coordinates = line[1].split(' ')[1:]
      destination_coordinates = line[2].split(' ')[1:]

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
      print(line)

    db_cursor.close()
    return

def connect_to_db():
  db_connection = psycopg2.connect(
    dbname=DB_NAME, 
    user=DB_USER, 
    password=DB_PASS,
    host = DB_HOST,
    port = DB_PORT
  )

  db_cursor = db_connection.cursor()

  db_cursor.execute(CREATE_TABLE_SCRIPT)
  db_connection.commit()

  db_cursor.close()

  return db_connection

if __name__ == "__main__":
  csv_path = sys.argv[1]
  db_connection = connect_to_db()
  load_csv_file_to_db(csv_path, db_connection.cursor())
  db_connection.commit()

  db_connection.close()