


def create_cat_level(df,cat_lvl_1 , cat_lvl_2):

    df['CATEGORY_LEVEL'] = df[cat_lvl_1].fillna('') + '_' + df[cat_lvl_2].fillna('')
    df['tmp'] = df['CATEGORY_LEVEL'].str.lower()

    df.loc[(df['tmp'].str.contains('accessoire') | df['tmp'].str.contains('zubehör')), ['CATEGORY_LEVEL']] = 'Accessoire'
    df.loc[(df['tmp'].str.contains('wimpern')), ['CATEGORY_LEVEL']] = 'Pflege_Augenpflege'
    df.loc[(df['tmp'].str.contains('nischenpflege') | df['tmp'].str.contains('detox') | df['tmp'].str.contains('anti-aging')), ['CATEGORY_LEVEL']] = 'Pflege_Gesichtspflege'
    df.loc[(df['tmp'].str.contains('sonnen')), ['CATEGORY_LEVEL']] = 'Sonnenpflege'

    df.drop('tmp', axis=1, inplace=True)
    return df

