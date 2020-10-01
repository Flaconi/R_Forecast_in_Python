
import pip
import os
import pandas as pd
import numpy as np
import importlib
import time
from sklearn import preprocessing
import sys
import datetime as dt
from datetime import timedelta
from datetime import date
import importlib
import pyexasol

from dotenv import load_dotenv , find_dotenv
load_dotenv(find_dotenv())

database_dev = "dwh-db01.foxtrot.aws.flaconi.net"
EXASOL_USERNAME = os.getenv("EXASOL_USERNAME", "DS_SERVICE")
EXASOL_PASSWORD = os.getenv("EXASOL_PASSWORD", "")
EXASOL_PASSWORD2 = os.getenv("EXASOL_PASSWORD2", "")
#connection_dev = pyexasol.connect(dsn=database_dev, user=EXASOL_USERNAME, password=EXASOL_PASSWORD2, compression=True)
database_prod = "dwh-db01.aws.flaconi.net"
#connection_prod = pyexasol.connect(dsn=database_prod, user=EXASOL_USERNAME, password=EXASOL_PASSWORD, compression=True)


# Update clusters
perform_cluster = False

# Desired length of seasonality forecast (can be adjusted seperately for DeepAR and Clusters)
years = 2
weeks = 52


###############################################
## Read Exasol data
###############################################
today = date.today()
this_monday = today - timedelta(days = today.weekday())

from src.Seasonality.utils.readers.read import read_input_data

df = read_input_data(EXASOL_USERNAME, EXASOL_PASSWORD, database_prod, this_monday)


######################################################################
## Additive Time Series Decomposition Total Sales to be Used by DeepAR
######################################################################
#from importlib import reload
#importlib.reload(sys.modules['Seasonality.Total_Seasonality.Total_Seasonality'])
from src.Seasonality.model.total_seasonality.total_seasonality import compute_total_seasonality

df_total = compute_total_seasonality(df, years = years, weeks = weeks, target = 'SALES_NORM',window_size = 5)

from src.Seasonality.utils.writers.write import write_table_to_db

#write to database
write_table_to_db(df_total, EXASOL_USERNAME, EXASOL_PASSWORD2, database_dev, data_schema= 'TEST_SANDBOX',
                      table_name= 'SKU_FCST_DEEPAR_SEASONALITY')


#####################################################
## Define Clusters and Compute Seasonal Decomposition
#####################################################

#from importlib import reload
#importlib.reload(sys.modules['Seasonality.Transform.Transform'])
from src.Seasonality.transform.transform import create_cat_level

# Create input clusters based on category level 1 and 2
df = create_cat_level(df, 'CATEGORY_LEVEL_1', 'CATEGORY_LEVEL_2')


from src.Seasonality.model.cluster.cluster import cluster_category_levels

# Update clusters of category levels
seas_groups = cluster_category_levels(df, perform_cluster = perform_cluster, cat_lvl = 'CATEGORY_LEVEL', clusters = 8 )


from src.Seasonality.model.cluster_seasonality.cluster_seasonality import compute_seasonal_decomposition

# Decompose log average sales per product in each cluster
result_list = compute_seasonal_decomposition(df, seas_groups,cat_lvl = 'CATEGORY_LEVEL',target_var = 'LOG_SALES_NORM',
                                              years = years, weeks = weeks)

#write to database
write_table_to_db(result_list, EXASOL_USERNAME, EXASOL_PASSWORD2, database_dev, data_schema= 'TEST_SANDBOX',
                      table_name= 'SKU_FCST_SEASONALITY')