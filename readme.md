A continuacion se encuentra la solucion al _Challenge Software Engineer_ para neuralworks.

En este readme, se explicara como ejecutar los scripts necesarios, ademas de el razonamiento detras de de ellos y las suposiciones tomadas en las soluciones.

Dentro de este repositorio se encuentra un archivo de `docker-compose` para correr contenedores (Uno conteniendo _python_, otro conteniendo _postgreSQL_ y otro conteniendo _PGAdmin4_, el que se encuentra comentado en caso que lo quieran activar.)

# Requisitos
Se necesita tener instalado docker y docker compose, para correr los contenedores, es necesario crear una carpeta llamada `data` y correr lo siguiente en la carpeta base

``` docker-compose up --build ```

Durante el proceso de construccion de la imagen y contenedor de `python` se descargan las librerias necesarias para la ejecucion correcta de los scripts.

Las librerias utilizadas en los scripts son las siguientes:

* `pandas` (Para transformar y manejar data)
* `psycopg2` (Para conectarse a la base de datos PostgreSQL)
* `fastapi` (Genera una API)
* `uvicorn` (Servidor que hostea la API)

Al iniciar los contenedores, se podra acceder a la api desde el contenedor de python (localizada en `localhost:8000`) donde se puede obtener la siguiente informacion:

* Cantidad semanal de la cantidad de viajes realizados dentro de un area definida por un bounding box y region.
* Estado de la ingesta de datos, mediante la cantidad de registros cargados a la base de datos y la fecha de la ultima carga. 

Para realizar la carga de datos a la base de datos y obtener el agrupamiento de los viajes similares, se deben ejecutar otros scripts dentro del container de python.

Primero hablaremos del servicio y script para procesar nuevos datos de viajes:

# Procesos automatizados para ingerir y almacenar los datos bajo demanda

Para empezar a poblar la base de datos, es necesario primero crear la base de datos con nombre `neuralworks`. El script se asegura de crear la tabla relacionada a los viajes (si es que esta no existe) cada vez que se realiza una conexion nueva a la base de datos.

El archivo `db.py` es utilizado para crear las tabla necesaria en la base de datos y poblarla con la data presente en el archivo csv presente en `./csv/travels.csv`. Ademas dentro de este se encuentra una abstraccion de la conexion a la base de datos mediante una clase llamada DB, la que es usada dentro de los otros scripts.

Para ejecutar el archivo es necesario correr `db.py ruta_al_csv` desde la terminal del contendor de docker (la ruta deberia ser `./csv/trips.csv`). Si se quiere ejecutar fuera del contenedor, se debe ejecutar

``` docker-compose run -it python python scripts/db.py csv/trips.csv ```

## Posibles mejoras

Una de las mejoras que se puede hacer al script es un mejor manejo de errores ademas de acceder a la base de datos utilizando ORM como `peewee` para abstraer mas la conexion a la base de datos permitiendo poder cambiar a otras base de datos relacionales sin tener que modificar mucho del codigo.

Otra forma de mejorar puede ser poder obtener los valores para la conexion a la base de datos mediante variables de entorno, por ahora estos valores se encuentran dentro del script (si quieren correr los scripts fuera del container, cambiando el host de la base de datos desde `db` a `localhost`).

Ademas hace falta tener los logs de la carga en un archivo en el caso que esta carga se haga automatica dentro de un `cron`.

# Agrupación

Se realiza una agrupacion de los viajes que son considerando el origen, destino y una hora del dia.

Primero los datos de la base de datos se ordenan por region y hora del dia, luego se itera por cada subgrupo de este calculando la diferencia entre la latitudes y longitudes de origen y destino de cada par de viajes basado en un _threshold_, como se ve a continuacion:

```
|longitud_origen_viaje1 - longitud_origen_viaje2| < THRESHOLD
```

El _threshold_ considerado es 0.05, lo que equivale aproximadamente a 5.55 KM segun la informacion presente en el siguiente link <http://wiki.gis.com/wiki/index.php/Decimal_degrees>. Lo siguiente nos da un bounding box con una longitud de 11.1 KM en cada arista.

Para obtener estos viajes cercanos, se debe ejecutar el archivo `grouping.py`, el que imprimira en pantalla una lista que contiene viajes y una sublista de los viajes que son cercanos a este. Como esta cercania de viajes es simetrica (si el viaje 1 es cercano al viaje 2, entonces el viaje 2 es cercano al viaje 1), se itera desde el primer viaje y se le compara con todos los viajes siguientes en la lista, evitando realizar calculos de mas.

## Posibles mejoras

Una muy importante mejora, tiene que ver con la forma en que se entrega la informacion, por razones de tiempo, no se pudo realizar un formateo mas legible de la informacion presente, queriendo especialmente entregarla en formato JSON, para que sea mas legible por un humano.

# Api

En el archivo `api.py` se encuentra una api creada con la libreria `fastAPI`, la que permite implementar APIs de manera rapida y eficiente usando python.

Al ejecutar el contenedor de `python`, la api se ejecuta al inicio de este, quedando disponible en la direccion `localhost:8000`. Si se quiere ejecutar la api desde fuera del contenedor, se debe tener instalado la libreria `uvicorn` (`pip install "uvicorn[standard]"`) y ejecutarla con el siguiente comando.

```  
uvicorn scripts.api:app
```

Los recursos de la api son los siguientes:

* `/weekly_travel_resume/{region}?min_latitude={latitud_minima}&max_latitude={latitud_maxima}&min_longitude{longitud_minima}&max_longitude={longitud_maxima}` 

  Este recurso retorna un JSON que contiene la cantidad de viajes de cada semana dentro de cada año, como se puede ver en el siguiente ejemplo:

  ```
  {
    "region": "Turin",
    "travels": [
        {
            "year": 2018,
            "travels": [
                {
                    "week_of_year": 18,
                    "travel_quantity": 16
                },
                {
                    "week_of_year": 19,
                    "travel_quantity": 12
                },
                {
                    "week_of_year": 20,
                    "travel_quantity": 12
                },
                {
                    "week_of_year": 21,
                    "travel_quantity": 28
                },
                {
                    "week_of_year": 22,
                    "travel_quantity": 8
                }
            ]
        }
    ]
  }
  ```

  No se hace una validacion de los datos, asi que es importante que los valores minimos sean menores que los maximos.

* `/data_ingest_state` 

  Esta llamada entrega informacion relacionada a la ultima fecha donde se realizo una carga de datos y la cantidad de registros cargados en esa fecha, en conjunto a la cantidad total de registros en la tabla

  ```
  {
    "last_uploaded_day": "2023-03-27T00:37:49.978971",
    "records_uploaded_on_last_day": 102,
    "total_records": 204
  }
  ```

# Solucion cloud para el proyecto

Debido a que este proyecto se encuentra en contenedores de docker (con posibilidad de pasar a kubernetes), es posible hacer un deploy de la base de datos y de la api Python (junto a los otros script) en una instancia de EC2 (o EK2) de AWS, o su simil en diferentes proveedores.

Para ejecutar el servicio de carga, se deberia cargar los contenedores en una instancia de servidor virtual y coordinar mediante `cron` la llamada al script de carga.

Debido a que los datos van a ser consultados en pocas ocaciones, esta solucion no seria la mas optima en terminos de costos, ya que se tendria ejecutando las instancias en servicios como amazon lambda u servicios de apis serverless.