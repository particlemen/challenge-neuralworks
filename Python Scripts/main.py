from fastapi import FastAPI 
from db import DB

app = FastAPI()

@app.get("/")
async def read_root():
  return {"Hello": "World"}