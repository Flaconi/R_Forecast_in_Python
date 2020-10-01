
import pandas as pd
import numpy as np
from datetime import timedelta
from statsmodels.tsa.seasonal import seasonal_decompose


def compute_total_seasonality(df, years=2, weeks=52, target='SALES_NORM', window_size=5):
    # Group data by week and compute average sales
    df_total = df.groupby('BEGIN_OF_WEEK').sum()
    df_total['SALES_NORM'] = df_total['QTY_CAPPED'] / df_total['NUM_INSTOCK_ITEMS']
    df_total['SALES'] = df_total['QTY_CAPPED']
    df_total.drop(['QTY_CAPPED', 'QTY', 'NUM_SOLD_ITEMS'], axis=1, inplace=True)

    # Add logs of sales
    df_total['LOG_SALES'] = np.log(df_total['SALES'] + 1)
    df_total['LOG_SALES_NORM'] = np.log(df_total['SALES_NORM'] + 1)
    df_total.sort_values(by='BEGIN_OF_WEEK')

    # setting Frequency of data
    df_total.index = pd.to_datetime(df_total.index)
    df_total.index.freq = 'W-MON'

    # Taking average sales
    ts = df_total[target]

    # Decompose average sales per product
    #from statsmodels.tsa.seasonal import seasonal_decompose

    result = seasonal_decompose(ts, model='additive', period=52, extrapolate_trend='freq')
    s = result.seasonal.to_frame()

    # Extract seasonal component from fitted data and replicate to prediction time horizon
    last_year = result.seasonal.tail(weeks)
    Last_year = pd.DataFrame(data=last_year.values, columns=['seasonal'])

    year2_seasonal = pd.concat([Last_year, Last_year], ignore_index=True)

    # Create dates for prediction time horizon
    last_date = df_total.index.max() + timedelta(days=7)
    prediction_dates = pd.DataFrame(pd.date_range(last_date, periods=weeks * years, freq='W-MON'),
                                    columns=['BEGIN_OF_WEEK'])

    # Create table
    Pred_time = pd.concat([prediction_dates, year2_seasonal], axis=1, sort=False)
    Pred_time.set_index("BEGIN_OF_WEEK", inplace=True)
    Pred_time.index.freq = 'W-MON'

    w = pd.concat([s, Pred_time], ignore_index=False)

    # Moving Average
    w['MovAvg28'] = w.rolling(window_size, center=True).mean()

    # Use smoothed seasonal component outside of Christmas period
    w.loc[(w.index.month == 12) | ((w.index.month == 1) & (w.index.day <= 21)), 'SMOOTH_SEASONALITY'] = w['seasonal']
    w.loc[(w.index.month != 12) | ((w.index.month == 1) & (w.index.day > 21)), 'SMOOTH_SEASONALITY'] = w['MovAvg28']

    w['SMOOTH_SEASONALITY'].fillna(w['seasonal'], inplace=True)
    w.reset_index(inplace=True)

    return w[['BEGIN_OF_WEEK','SMOOTH_SEASONALITY']]

