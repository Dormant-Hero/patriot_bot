import os
from dotenv import load_dotenv

load_dotenv()

def _required(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


OWNER_ID = int(_required("OWNER_ID"))
# testing enviornment_variables
DB_NAME = _required("TEST_DBNAME")
PATRIOTS_ROLE_ID = int(_required("PATRIOT_ROLE_ID"))
DB_USER = _required("USERNME")
DB_PASSWORD = _required("PASSWORD")
DB_HOST = _required("HOST")
DB_PORT = _required("PORT")
DB_CONNECTION_STRING = f"dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} host={DB_HOST} port={DB_PORT}"
TOKEN = _required("TEST_TOKEN")