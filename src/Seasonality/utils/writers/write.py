import pandas as pd
import pyexasol

def create_connection(username, password, database, database_schema=None):
    '''
    Given the parameters returns a connection to an exasol database
    Parameters
    ----------
    username: str
    password: str
    database: str
    database_schema: str

    Returns
    -------
    Returns a connection to an exasol database
    '''
    if database_schema is not None:
        return pyexasol.connect(dsn=database, user=username, password=password, schema=database_schema, compression=True)
    else:
        return pyexasol.connect(dsn=database, user=username, password=password, compression=True)


def derive_schema(data):
    '''
    Helper function to extract the schema of a DataFrame if this want be put in the Database
    Parameters
    ----------
    data: DataFrame
        Generic DataFrame

    Returns
    -------
    schema_string: string
        Schema required to create a table with the same structure in the DB as the DF

    '''
    schema = pd.DataFrame(data.dtypes).reset_index()
    schema.loc[schema[0] == 'float64', 0] = "DECIMAL(36, 15)"
    schema.loc[schema[0] == 'int64', 0] = "DECIMAL(18,0)"
    schema.loc[schema[0] == 'object', 0] = "varchar(600)"
    schema.loc[schema[0] == 'datetime64[ns]', 0] = "Date"
    schema_string = ""

    for i in range(0, schema.shape[0] - 1):
        schema_string = schema_string + str(schema.loc[i, "index"]) + " " + str(schema.loc[i, 0]) + ", "
    schema_string = schema_string + str(schema.loc[schema.shape[0] - 1, "index"]) + " " + str(
        schema.loc[schema.shape[0] - 1, 0])
    return schema_string

def write_table_to_db(category_attributes, username, password, database, data_schema,
                      table_name):
    connection = create_connection(username=username, password=password, database=database,
                                   database_schema=data_schema)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS " + data_schema + "." + table_name + " (" +
        derive_schema(category_attributes)
        + ");")
    connection.execute("TRUNCATE TABLE " + data_schema + "." + table_name + ";")
    connection.import_from_pandas(category_attributes, table=table_name)



