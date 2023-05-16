import os
from dotenv import load_dotenv

load_dotenv()

#app configs
app_host = os.getenv('HOST')
app_port = os.getenv('PORT')

#database_configs
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
