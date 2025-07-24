from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Read credentials from environment
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
DATABASE = os.getenv("DB_NAME")
TABLE = "sales"

# Create the connection string
DB_URI = f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{DATABASE}"
engine = create_engine(DB_URI)

def fetch_sales_data():
    """
    Fetches all records from the 'sales' table into a DataFrame.
    """
    query = f"SELECT * FROM {TABLE}"
    df = pd.read_sql(query, engine)
    return df
