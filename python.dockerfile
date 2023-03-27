FROM python:3.10.10
# Or any preferred Python version.
WORKDIR /home/
ADD scripts /home/scripts
ADD csv /home/csv 
RUN pip install fastapi psycopg2 "uvicorn[standard]" pandas
CMD ["uvicorn", "scripts.api:app", "--host", "0.0.0.0", "--port", "8000"] 