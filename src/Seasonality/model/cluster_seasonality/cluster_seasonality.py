
import pip
import pyexasol
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
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def compute_seasonal_decomposition(df, seas_groups, cat_lvl = 'CATEGORY_LEVEL',target_var = 'LOG_SALES_NORM',
                                   years = 2, weeks = 52):
    Result = pd.DataFrame(columns=['BEGIN_OF_WEEK', 'SEASONALITY', 'CLUSTER'])

    for i in seas_groups['Cluster'].unique():
        sales_df = pd.merge(df[df['BEGIN_OF_WEEK'] >= '2016-01-01'], seas_groups[seas_groups['Cluster'] == i],
                            how='inner', on=['CATEGORY_LEVEL'])

        sales_df = sales_df.groupby(['BEGIN_OF_WEEK']).sum()

        sales_df['SALES_NORM'] = sales_df['QTY_CAPPED'] / sales_df['NUM_INSTOCK_ITEMS']
        sales_df['SALES'] = sales_df['QTY_CAPPED']

        sales_df.drop(['QTY', 'NUM_INSTOCK_ITEMS', 'QTY_CAPPED', 'NUM_SOLD_ITEMS'], axis=1, inplace=True)

        min = sales_df.index.min()
        max = sales_df.index.max()
        df_dates = pd.DataFrame(pd.date_range(min, max, freq='W-MON'), columns=['BEGIN_OF_WEEK'])

        sales_df = df_dates.merge(sales_df, on=['BEGIN_OF_WEEK'], how='left').fillna(0)

        sales_df['LOG_SALES'] = np.log(sales_df['SALES'] + 1)
        sales_df['LOG_SALES_NORM'] = np.log(sales_df['SALES_NORM'] + 1)

        sales_df.set_index('BEGIN_OF_WEEK', inplace=True)
        sales_df.index = pd.to_datetime(sales_df.index)
        sales_df.index.freq = 'W-MON'

        ts = sales_df['LOG_SALES_NORM']

        result = seasonal_decompose(ts, model='additive', period=52, extrapolate_trend='freq')

        sales_df = pd.concat([sales_df, result.seasonal], axis=1, sort=False)
        sales_df = pd.concat([sales_df, result.trend], axis=1, sort=False)

        exp_model = ExponentialSmoothing(ts, trend='add', seasonal='add', seasonal_periods=52).fit()
        test = pd.DataFrame(exp_model.forecast(years * weeks), columns=['Value'])

        fitted_value = pd.DataFrame(exp_model.fittedvalues, columns=['Value'])

        write_df = pd.concat([fitted_value, test])
        write_df = write_df.reset_index().rename(columns={'index': 'BEGIN_OF_WEEK'})

        SEASONALITY = pd.DataFrame(columns=['BEGIN_OF_WEEK', 'SEASONALITY', 'CLUSTER'])

        SEASONALITY['BEGIN_OF_WEEK'] = write_df['BEGIN_OF_WEEK']
        # Seasonality will be transformed back due to using log average sales
        SEASONALITY['SEASONALITY'] = np.expm1(write_df['Value'])
        SEASONALITY['CLUSTER'] = i


        Result = Result.append(SEASONALITY, ignore_index=True)

    return Result





