# File Objective: List latest water readings for each active water connection
# 1. Import libraries to use
from mysql.connector import MySQLConnection, connect
from mysql.connector.cursor import MySQLCursorDict
import pandas as pd
from pandas import DataFrame, merge
from datetime import date, datetime
#
# 1.1. Set display options for pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)


#
# 2. Initialize the database connection
# Define function to initialize Database (DB) connection
# The function returns a tuple of mixed types (MySQLConnection, MySQLCursorDict,
#   and the pd module).
def init() -> tuple[MySQLConnection, MySQLCursorDict]:
    #
    # 2.3. Connect to the database
    # 2.3.1. Store database connection configuration arguments in a dictionary
    config: dict[str, str] = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'mutall_rental',
    }
    #
    # 2.3.2. Unpack the configurations dictionary above to connect to the
    # database
    conn: MySQLConnection = connect(**config)
    #
    # 2.4. Create a cursor object to interact with the connected database
    # Set the cursor object to always return query results in a list instead of
    #   a tuple
    cursor: MySQLCursorDict = conn.cursor(dictionary=True)
    #
    # Return the connection and cursor objects in a tuple to use them
    #   outside the init function
    return conn, cursor


#
# 3. Call the init function
# Access the connection, cursor, and pd by assigning the return values of init
#   to variables
[konekshon, kasa] = init()


#
# 4. Define a function to calculate the current water readings for each water
#   connection
# The function returns a DataFrame
def get_current_readings() -> DataFrame:
    #
    # 4.1. Execute query database for all water connections
    kasa.execute("select * from wconnection")
    #
    # 4.2. Fetch the returning result (i.e., a list of dictionaries|rows)
    all_water_connections = kasa.fetchall()
    #
    # 4.3. Create dataframe of water connections using Pandas
    water_connection_df = DataFrame(all_water_connections)
    #
    # 4.4. Filter dataframe to have only active water connections
    filter_date = date(9999, 12, 31)
    active_water_connections_df = water_connection_df[
        water_connection_df['end_date'] == filter_date]
    #
    # 4.5. Execute query DB for all water meters
    kasa.execute("select * from wmeter")
    #
    # 4.6. Fetch the returning result
    all_water_meters = kasa.fetchall()
    #
    # 4.7. Create dataframe of water meters using Pandas
    water_meters_df = DataFrame(all_water_meters)
    #
    # 4.8. Execute query DB for all water readings
    kasa.execute("select * from wreading")
    #
    # 4.9. Fetch the returning result (i.e., a list of dictionaries|rows)
    all_water_readings = kasa.fetchall()
    #
    # 4.10. Create dataframe of water readings using Pandas
    water_readings_df = DataFrame(all_water_readings)
    #
    # 4.11. Join dataframes
    #
    # 4.11.1. Join the active water connections dataframe to the water meters
    # dataframe
    water_connections_and_meters_df = merge(
        active_water_connections_df, water_meters_df, on='wmeter', how='inner'
    )
    # 4.11.2. Join the active water connections and water meters dataframe to
    # the water readings dataframe
    all_water_connection_readings = merge(
        water_connections_and_meters_df,
        water_readings_df,
        on='wmeter',
        how='inner'
    )
    #
    # 4.12. Get maximum date for each water connection
    # 4.12.1. Group dataframe by water connection
    grouped_water_connections_df = all_water_connection_readings.groupby(
        'wconnection'
    )
    #
    # 4.12.2. Get the row INDEX of the maximum water reading date for each water
    # connection
    # Index - identifier|label for each row in a dataframe
    max_dates_indices = grouped_water_connections_df['date'].idxmax()
    #
    # 4.12.3. Use .loc to get the rows that match the indices above
    latest_readings_df = all_water_connection_readings.loc[max_dates_indices]
    #
    # 4.13. Filter columns to show
    latest_readings_df = latest_readings_df[
        ['wconnection', 'rate', 'date', 'value']
    ]
    # 4.14. Rename column names
    latest_readings_df = latest_readings_df.rename(
        columns={
            'date': 'curr_date',
            'value': 'curr_value'
        }
    )
    return latest_readings_df


#
# 5. Define function to retrieve previous readings for each water connection
# The function returns a DataFrame
def get_previous_readings() -> DataFrame:
    # 5.1. Get last invoice period
    #
    # 5.1.1. Execute query on database
    kasa.execute("select * from period")
    #
    # 5.1.2. Fetch the results from Database
    all_periods = kasa.fetchall()
    #
    # 5.1.3. Create a Dataframe from the fetched result
    periods_df = DataFrame(all_periods)
    #
    # 5.1.4. Get today's date
    leo = datetime.today()
    #
    # 5.1.5. Get previous invoice date
    # Based on today's date (month), get the period of last month
    last_period_df = periods_df[
        (periods_df['month'] == leo.month - 1)
        & (periods_df['year'] == leo.year)
        ]
    # 5.1.6. Access cutoff date
    cutoff_date = last_period_df.iloc[0]['cutoff']
    #
    # 5.2. Get water readings on based on the invoice|cutoff period
    # 5.2.1. Execute query on database
    kasa.execute("select * from water")
    #
    # 5.2.2. Fetch the result of the query from database
    all_invoiced_water_readings = kasa.fetchall()
    #
    # 5.2.3. Create a dataframe from the fetched result
    all_invoiced_water_readings_df = DataFrame(all_invoiced_water_readings)
    #
    # 5.2.4. Filter the dataframe to have only rows of the last invoice date|
    # cutoff date
    last_invoiced_water_readings_df = all_invoiced_water_readings_df[
        all_invoiced_water_readings_df['curr_date'] == cutoff_date
        ]
    #
    # 5.3. Filter the columns to be displayed
    last_invoiced_water_readings_df = last_invoiced_water_readings_df[
        ['wconnection', 'curr_date', 'curr_value']
    ]
    #
    # 5.4. Rename the column names
    last_invoiced_water_readings_df = last_invoiced_water_readings_df.rename(
        columns={
            'curr_date': 'prev_date',
            'curr_value': 'prev_date'
        }
    )
    return last_invoiced_water_readings_df


curr_rds = get_current_readings()
prev_rds = get_previous_readings()
print(' ')
