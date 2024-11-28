# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the service charges
#
# 1. Import libraries to use
from mysql.connector import MySQLConnection, connect
from mysql.connector.cursor import MySQLCursorDict
import pandas as pd
from pandas import DataFrame, merge
from pandas.core.groupby.generic import DataFrameGroupBy
from datetime import date, datetime
#
# 1.1. Set display options for pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)


#
# 2. Initialize the database connection
# 2.1. Define function to initialize Database (DB) connection
# The function returns a tuple of mixed types (MySQLConnection, MySQLCursorDict,
#   and the pd module).
def init() -> tuple[MySQLConnection, MySQLCursorDict]:
    #
    # 2.2. Connect to the database
    # 2.2.1. Store database connection configuration arguments in a dictionary
    config: dict[str, str] = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'mutall_rental',
    }
    #
    # 2.2.2. Unpack the configurations dictionary above to connect to the
    # database and assigning the database connection object to a variable
    conn: MySQLConnection = connect(**config)
    #
    # 2.3. Create a cursor object to interact with the connected database
    # Set the cursor object to always return query results in a list instead of
    #   a tuple
    # Cursor object returns each row as a dictionary
    cursor: MySQLCursorDict = conn.cursor(dictionary=True)
    #
    # 2.4. Return the connection and cursor objects in a tuple to use them
    #   outside the init function
    return conn, cursor


#
# 3. Call the init function
# Unpack the returned tuple that contains the connection and cursor objects -by
#   assigning the return values of init to variables
[konekshon, kasa] = init()
#
# Group global variables to pass to the class constructor method


#
# 4. Define a class that encapsulates the water table
class Water:
    def __init__(self):
        pass
    #
    # 4.1. Define the constructor method
    #
    # 4.2. Define the methods of the class
    # 4.2.1. Define method to get current water readings for each water
    #   connection
    @staticmethod
    def get_current_readings() -> DataFrame:
        #
        # 4.2.1.1. Execute query on database
        kasa.execute("select * from wconnection")
        #
        # 4.2.1.2. Fetch and store the query result from database
        all_water_connections: list[dict] = kasa.fetchall()
        #
        # 4.2.1.3. Create a DataFrame from the result
        all_water_connections_df: DataFrame = DataFrame(all_water_connections)
        #
        # 4.4. Filter dataframe to have only active water connections
        filter_date: date = date(9999, 12, 31)
        active_water_connections_df: DataFrame = all_water_connections_df[
            all_water_connections_df['end_date'] == filter_date]
        #
        # 4.5. Execute query DB for all water meters
        kasa.execute("select * from wmeter")
        #
        # 4.6. Fetch the returning result
        all_water_meters: list[dict] = kasa.fetchall()
        #
        # 4.7. Create dataframe of water meters using Pandas
        water_meters_df: DataFrame = DataFrame(all_water_meters)
        #
        # 4.8. Execute query DB for all water readings
        kasa.execute("select * from wreading")
        #
        # 4.9. Fetch the returning result (i.e., a list of dictionaries|rows)
        all_water_readings: list[dict] = kasa.fetchall()
        #
        # 4.10. Create dataframe of water readings using Pandas
        water_readings_df: DataFrame = DataFrame(all_water_readings)
        #
        # 4.11. Join dataframes for water connection, water meter, and water
        # reading tables
        #
        # 4.11.1. Join the active water connections dataframe to the water
        # meters dataframe
        water_connections_and_meters_df: DataFrame = merge(
            active_water_connections_df, water_meters_df, on='wmeter',
            how='inner'
        )
        # 4.11.2. Join the active water connections and water meters dataframe
        # to the water readings dataframe
        all_water_connection_readings: DataFrame = merge(
            water_connections_and_meters_df,
            water_readings_df,
            on='wmeter',
            how='inner'
        )
        #
        # 4.12. Get maximum date for each water connection
        # 4.12.1. Group dataframe by water connection
        grouped_water_connections_df: DataFrameGroupBy = (
            all_water_connection_readings.groupby('wconnection')
        )
        #
        # 4.12.2. Get the row INDEX of the maximum water reading date for each
        # water connection
        # Index - identifier|label for each row in a dataframe
        max_dates_indices: DataFrame = (
            grouped_water_connections_df['date'].idxmax()
        )
        #
        # 4.12.3. Use .loc to get the rows that match the indices above
        latest_readings_df: DataFrame = all_water_connection_readings.loc[
            max_dates_indices]
        #
        # 4.13. Filter columns to show
        latest_readings_df: DataFrame = latest_readings_df[
            ['wconnection', 'serial_no', 'rate', 'date', 'value']
        ]
        # 4.14. Rename column names
        latest_readings_df: DataFrame = latest_readings_df.rename(
            columns={
                'date': 'curr_date',
                'value': 'curr_value'
            }
        )
        return latest_readings_df

    #
    # 4.2.2. Define method to get previous water readings for each water
    #   connection
    @staticmethod
    def get_previous_readings() -> DataFrame:
        # 5.1. Get last invoice period
        #
        # 5.1.1. Execute query on database
        kasa.execute("select * from period")
        #
        # 5.1.2. Fetch the results from Database
        all_periods: list[dict] = kasa.fetchall()
        #
        # 5.1.3. Create a Dataframe from the fetched result
        periods_df: DataFrame = DataFrame(all_periods)
        #
        # 5.1.4. Get today's date
        leo: datetime = datetime.today()
        #
        # 5.1.5. Get previous invoice date
        # Based on today's date (month), get the period of last month
        last_period_df: DataFrame = periods_df[
            (periods_df['month'] == leo.month - 1)
            & (periods_df['year'] == leo.year)
            ]
        # 5.1.6. Access cutoff date
        cutoff_date: date = last_period_df.iloc[0]['cutoff']
        #
        # 5.2. Get water readings on based on the invoice|cutoff period
        # 5.2.1. Execute query on database
        kasa.execute("select * from water")
        #
        # 5.2.2. Fetch the result of the query from database
        all_invoiced_water_readings: list[dict] = kasa.fetchall()
        #
        # 5.2.3. Create a dataframe from the fetched result
        all_invoiced_water_readings_df: DataFrame = DataFrame(
            all_invoiced_water_readings
        )
        #
        # 5.2.4. Filter the dataframe to have only rows of the last invoice date
        # |cutoff date
        last_invoiced_water_readings_df: DataFrame = all_invoiced_water_readings_df[
            all_invoiced_water_readings_df['curr_date'] == cutoff_date
            ]
        #
        # 5.3. Filter the columns to be displayed
        last_invoiced_water_readings_df: DataFrame = (
            last_invoiced_water_readings_df[
                ['wconnection', 'curr_date', 'curr_value']
            ]
        )
        #
        # 5.4. Rename the column names
        last_invoiced_water_readings_df: DataFrame = (
            last_invoiced_water_readings_df.rename(columns={
                    'curr_date': 'prev_date',
                    'curr_value': 'prev_value'
                }
            )
        )

        return last_invoiced_water_readings_df

    #
    # 4.2.3. Define method that calculates the daily average consumption and
    #   total amount to invoice each water connection
    def get_calculations(self) -> DataFrame:
        #
        # 6.1. Join the current readings and previous readings DataFrames
        curr_and_prev_rds: DataFrame = merge(
            self.get_previous_readings(),
            self.get_current_readings(),
            on='wconnection',
            how='inner'
        )
        #
        # 6.2. Add column to calculate the number of days that water was
        # consumed after the last reading for each water connection
        #
        # 6.2.1. Change the current and previous dates to datetime types in
        # Pandas so that we can perform arithmetics on them
        curr_and_prev_rds['prev_date'] = pd.to_datetime(
            curr_and_prev_rds['prev_date'])
        curr_and_prev_rds['curr_date'] = pd.to_datetime(
            curr_and_prev_rds['curr_date'])
        #
        # 6.2.2. Subtract the previous date from the current date to get the
        #   number of days
        # Use the 'days' property to transform the return value from a Timedelta
        #   object to an integer
        curr_and_prev_rds['consumption_days'] = (
                curr_and_prev_rds['curr_date'] - curr_and_prev_rds['prev_date']
        ).dt.days
        #
        # 6.3. Add column to calculate the total water consumption for each
        # water connection
        curr_and_prev_rds['total_consumption'] = (
                curr_and_prev_rds['curr_value']
                - curr_and_prev_rds['prev_value']
        )
        #
        # 6.4. Add column to calculate the average daily consumption for each
        # water connection
        curr_and_prev_rds['avg_daily_cons'] = (
                curr_and_prev_rds['total_consumption'] / curr_and_prev_rds[
                    'consumption_days']
        )
        #
        # 6.5. Add column to calculate the amount each water connection is
        # supposed to be invoiced
        curr_and_prev_rds['amount'] = (
                curr_and_prev_rds['total_consumption'] * curr_and_prev_rds[
                    'rate']
        )
        # 6.6. Reorder the columns
        curr_and_prev_rds: DataFrame = curr_and_prev_rds[
            ['wconnection', 'serial_no', 'prev_date', 'prev_value', 'curr_date',
             'curr_value', 'consumption_days', 'total_consumption',
             'avg_daily_cons', 'rate', 'amount']]
        return curr_and_prev_rds


#
# Define a class for service charges calculations
class Service:
    #
    # Define constructor method
    def __init__(self):
        pass

    #
    # Define method that gets current subscriptions for each client
    @staticmethod
    def get_service() -> DataFrame:
        #
        # Get list of all clients
        kasa.execute("select name, client from client")
        #
        # Fetch results from database
        all_clients: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame from fetched result
        clients_df: DataFrame = DataFrame(all_clients)
        #
        # Get active clients
        # Join agreement table
        kasa.execute(
            """
                select
                    client,
                    start_date, 
                    `terminated`, 
                    valid,
                    agreement
                from 
                    agreement
            """
        )
        #
        # Fetch results from database
        agreements: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame for the agreements
        agreements_df: DataFrame = DataFrame(agreements)
        #
        # Get active clients
        # Join the clients and agreement DataFrames
        clients_and_agreements_df: DataFrame = merge(
            clients_df, agreements_df, on='client',
            how='inner'
        )
        #
        # Filter the joined client and agreement DataFrame
        active_clients_df: DataFrame = clients_and_agreements_df[(clients_and_agreements_df['valid'] == 1) &
                                                                 (clients_and_agreements_df['terminated'].isna())]

        #
        # Get subscription(s) for each active client
        kasa.execute("select subscription, client, service from subscription")
        subscriptions: list[dict] = kasa.fetchall()
        subscriptions_df: DataFrame = DataFrame(subscriptions)
        #
        # Join the subscription and active clients DataFrames
        client_subscriptions_df: DataFrame = merge(
            active_clients_df, subscriptions_df, on='client', how='inner'
        )
        #
        # Get the actual service details and join to the client-subscriptions DF
        kasa.execute("select name, service, price, auto from service")
        services: list[dict] = kasa.fetchall()
        services_df: DataFrame = DataFrame(services)
        #
        # Join client-subscription and services DataFrames
        client_sub_services_df: DataFrame = merge(
            client_subscriptions_df, services_df, on='service', how='inner'
        )
        return client_sub_services_df

client = Service()
cl = client.get_service()
print('f')