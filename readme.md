# Requisitos

Se necesitan las siguientes librerias de python:

* `psycopg2`
* `fastapi`
* `uvicorn` ( ``` pip install "uvicorn[standard]" ``` )

## Procesos automatizados para ingerir y almacenar los datos bajo demanda

El archivo `main.py` es utilizado para crear las tabla necesaria en la base de datos y poblarla con la data presente en el archivo csv necesario.

Para ejecutar el archivo es necesario correr `db.py ruta_al_csv` 

## Solucion cloud para el proyecto

Debido a que este proyecto se encuentra en contenedores de docker (con posibilidad de pasar a kubernetes), es posible hacer un deploy de la base de datos y de la api Python (junto a los otros script) en una instancia de EC2 (o EK2) de AWS, o su simil en diferentes proveedores.

Debido a que los datos van a ser consultados en pocas ocaciones, esta solucion no seria la mas optima en terminos de costos, ya que se tendria ejecutando las instancias 