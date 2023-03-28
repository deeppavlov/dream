import os  
from dotenv import load_dotenv

load_dotenv()

# TERMINUSDB_SERVER_DB = os.getenv("TERMINUSDB_SERVER_DB")
# TERMINUSDB_SERVER_TEAM = os.getenv("TERMINUSDB_SERVER_TEAM") 
# TERMINUSDB_SERVER_PASSWORD = os.getenv("TERMINUSDB_SERVER_PASSWORD")  
# TERMINUSDB_SERVER_URL = os.getenv("TERMINUSDB_SERVER_URL")

KG_DB_NAME = os.getenv("KG_DB_NAME")
KG_TEAM_NAME = os.getenv("KG_TEAM_NAME")
KG_PASSWORD = os.getenv("KG_PASSWORD")
KG_SERVER = os.getenv("KG_SERVER")