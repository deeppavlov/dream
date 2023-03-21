import os  
from dotenv import load_dotenv

load_dotenv()

KG_DB_NAME = os.getenv("KG_DB_NAME")
KG_TEAM_NAME = os.getenv("KG_TEAM_NAME") 
KG_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")  
KG_SERVER = os.getenv("TERMINUSDB_SERVER_URL")
