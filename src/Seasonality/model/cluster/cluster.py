
import pandas as pd
import numpy as np
from sklearn.preprocessing import scale
import scipy.cluster.hierarchy as sch
from sklearn.cluster import AgglomerativeClustering


def cluster_category_levels (df, perform_cluster, cat_lvl= 'CATEGORY_LEVEL', clusters = 8 ):

    df['BEGIN_OF_WEEK'] = pd.to_datetime(df['BEGIN_OF_WEEK'])
    # Group data by week and category level
    df_agg = df.groupby(['BEGIN_OF_WEEK', 'CATEGORY_LEVEL']).sum()

    # Add dates to Adventskalender category, as there is no stock throughout most of the year
    df_dates = pd.DataFrame(df_agg.index.get_level_values(0).unique(), columns=['BEGIN_OF_WEEK'])
    df_dates['key'] = 1

    Advent_name = pd.DataFrame(df[df['CATEGORY_LEVEL'].str.contains('Advent')]['CATEGORY_LEVEL'].unique(),
                               columns=['CATEGORY_LEVEL'])
    Advent_name['key'] = 1

    # Cross product of dates and catgories
    df_advent = pd.merge(df_dates, Advent_name, on='key')
    df_advent.drop(['key'], axis=1, inplace=True)

    df_advent = pd.merge(df_advent, df_agg, how='left', on=['CATEGORY_LEVEL', 'BEGIN_OF_WEEK'])
    df_advent = df_advent.fillna(0)

    df_agg.reset_index(inplace=True)

    # Add again to grouped data
    df_agg = pd.concat([df_agg, df_advent]).drop_duplicates()

    df_agg.sort_values(by=['CATEGORY_LEVEL', 'BEGIN_OF_WEEK'], inplace=True)


    if perform_cluster == True:
        # Clustering based on log(avg qty sold per instock item).
        df_agg['LOG_SALES_NORM'] = np.log((df_agg['QTY_CAPPED'] / df_agg['NUM_INSTOCK_ITEMS']) + 1)
        df_agg = df_agg.replace([np.inf, -np.inf], np.nan)
        df_agg['LOG_SALES_NORM'] = df_agg['LOG_SALES_NORM'].fillna(0)

        # Reshape data since 2018 to contain category levels in colums and weeks in rows
        df_reshape = df_agg[df_agg['BEGIN_OF_WEEK'].dt.year >= 2018]
        df_reshape = df_reshape.pivot(index='BEGIN_OF_WEEK', columns='CATEGORY_LEVEL', values='LOG_SALES_NORM')
        df_reshape.sort_values(by=['BEGIN_OF_WEEK'], inplace=True)
        df_reshape = df_reshape.fillna(0)

        # Standordise columns
        df_scale = pd.DataFrame(scale(df_reshape), columns=df_reshape.columns)
        df_scale.index = df_reshape.index

        # Dissimilarity between category levels besed on correlation of the time series
        df_corr = df_scale.corr()
        dissimilarty = ((1 - df_corr) * 2) ** .5

        # Hierachical clustering
        dendrogram = sch.dendrogram(sch.linkage(dissimilarty, method="ward"))

        cluster = AgglomerativeClustering(n_clusters=8, affinity='euclidean', linkage='ward')
        Cluster_mapping = cluster.fit_predict(dissimilarty)

        # Get category levels which belong to each cluster
        Cluster_mapping = pd.DataFrame(Cluster_mapping, columns=['Cluster'])
        Cluster_mapping.index = dissimilarty.index
        Cluster_mapping = Cluster_mapping.reset_index()

        Cluster_mapping['Cluster'] = 'SEAS_CLUSTER' + (Cluster_mapping['Cluster'] + 1).map(str)

    else:
        Cluster_mapping = pd.DataFrame(df_agg['CATEGORY_LEVEL'].unique(), columns=['CATEGORY_LEVEL'])

        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(
            ["Accessoire", "Make-up_Pinsel", "Pflege_Hand- & Fußpflege",
             "Make-up_Make-up Sets"]), 'Cluster'] = 'SEAS_CLUSTER1'
        Cluster_mapping.loc[
            Cluster_mapping['CATEGORY_LEVEL'].isin(["Sonstige_Adventskalender"]), 'Cluster'] = 'SEAS_CLUSTER2'
        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(
            ["Pflege_For Kids", "Pflege_Mama & Baby"]), 'Cluster'] = 'SEAS_CLUSTER3'
        Cluster_mapping.loc[
            Cluster_mapping['CATEGORY_LEVEL'].isin(["Haare_Haarstyling Tools"]), 'Cluster'] = 'SEAS_CLUSTER4'
        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(
            ["Haare_Styling", "Haare_Waschen & Pflegen", "Haare_Haarbürsten & Kämme", "Make-up_Nägel",
             "Pflege_Augenpflege", "Pflege_Gesichtspflege"]), 'Cluster'] = 'SEAS_CLUSTER5'
        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(
            ["Make-up_Augen", "Make-up_Lippen", "Make-up_Teint"]), 'Cluster'] = 'SEAS_CLUSTER6'
        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(
            ["Parfum_Damenparfum", "Parfum_Herrenparfum", "Haare_For Men", "Pflege_For Men",
             "Pflege_Körperpflege"]), 'Cluster'] = 'SEAS_CLUSTER7'
        Cluster_mapping.loc[Cluster_mapping['CATEGORY_LEVEL'].isin(["Sonnenpflege"]), 'Cluster'] = 'SEAS_CLUSTER8'

        Cluster_mapping = Cluster_mapping.dropna()

    return Cluster_mapping

