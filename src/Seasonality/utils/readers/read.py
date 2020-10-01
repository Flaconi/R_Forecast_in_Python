
import os
import pandas as pd
from datetime import timedelta
from datetime import date
import importlib
import pyexasol
import sys



def read_input_data(username, password, database, this_monday):
    query = ''' SELECT * FROM DS_PROJECTS.V_SKU_FCST_SEASONALITY_INPUT 
                WHERE BEGIN_OF_WEEK < '{}' '''.format(this_monday)
    connection_prod = pyexasol.connect(dsn=database, user=username, password=password,
                                       compression=True)
    df = connection_prod.export_to_pandas(query)
    df['BEGIN_OF_WEEK'] = pd.to_datetime(df['BEGIN_OF_WEEK'])

    return df