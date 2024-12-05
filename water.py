# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the service charges
#
# Import libraries to use
from mysql.connector import MySQLConnection, connect
from mysql.connector.cursor import MySQLCursorDict
import pandas as pd
from pandas import DataFrame, merge, to_datetime, Timestamp
from pandas.core.groupby.generic import DataFrameGroupBy
from datetime import date, datetime

#
# Set display options for pandas - to show all columns and full width
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)


#
# Configure the database connection
# - Define function to initialize Database (DB) connection
# - The function returns the connection and cursor objects in a tuple of mixed
#   types (MySQLConnection, and MySQLCursorDict).
def init() -> tuple[MySQLConnection, MySQLCursorDict]:
    #
    # Connect to the database
    # - Store database connection configuration arguments in a dictionary
    config: dict[str, str] = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'mutall_rental',
    }
    #
    # - Unpack the configurations dictionary above to connect to the database
    #   and assigning the database connection object to a variable
    conn: MySQLConnection = connect(**config)
    #
    # Create a cursor object to interact with the connected database
    # - Set the cursor object to always return query results in a list instead
    #   of the default (tuple)
    # - Cursor object returns each row as a dictionary|object
    cursor: MySQLCursorDict = conn.cursor(dictionary=True)
    #
    # - Return the connection and cursor objects in a tuple to use them
    #   outside the init function
    return conn, cursor


#
# Initialize the database connection
# - Unpack the returned tuple that contains the connection and cursor objects
#   then assign the return values of init to global variables
[konekshon, kasa] = init()


#
# Define a class that encapsulates all the clients to be invoiced this month
class Client:
    #
    # Define the constructor method
    def __init__(self):
        pass

    # Define the methods of the class
    #
    # Define method that gets active clients
    @staticmethod
    def get_active_clients() -> DataFrame:
        #
        # Get list of all clients from the database
        kasa.execute("select client, name, quarterly from client")
        #
        # Fetch results from the database
        all_clients: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame from fetched result
        all_clients_df: DataFrame = DataFrame(all_clients)
        #
        # Get list of all agreements from the Database
        kasa.execute(
            """
                select
                    client,
                    start_date, 
                    `terminated`, 
                    valid
                from 
                    agreement
            """
        )
        #
        # Fetch results from the database
        agreements: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame for the fetched result
        agreements_df: DataFrame = DataFrame(agreements)
        #
        # Convert agreement start date to standard date format
        agreements_df['start_date'] = to_datetime(agreements_df['start_date'])
        #
        # Get the active clients - whose agreements are valid and not terminated
        # - Join the clients and agreement DataFrames
        clients_and_agreements_df: DataFrame = merge(
            all_clients_df, agreements_df, on='client',
            how='inner'
        )
        #
        # - Filter the joined client and agreement DataFrame
        # - Only return clients whose agreements are valid and are not
        #   terminated
        active_clients_df: DataFrame = clients_and_agreements_df[
            (clients_and_agreements_df['valid'] == 1) &
            (clients_and_agreements_df['terminated'].isna())]

        return active_clients_df

    # Get clients that should be invoiced this month
    # - Only active clients that pay monthly and those who pay quarterly and
    #   paid 3 months ago
    def get_clients_to_invoice(self):
        #
        # Convert today's date to standard date format
        today: Timestamp = to_datetime(datetime.today())
        #
        # Select clients who are invoiced monthly together with the quarterly
        #   clients that are to be invoiced this month
        clients: DataFrame = self.get_active_clients()
        clients_to_invoice_df: DataFrame = clients[
            #
            # Return the monthly clients
            (clients['quarterly'] == 0)
            #
            # Return the quarterly clients that should be invoiced this month
            | (
                    (clients['quarterly'] == 1)
                    & (
                        #
                        # Get the difference in months between today and
                        # agreement start date and get the modulus of the result
                        ((today.year - clients['start_date'].dt.year) * 12)
                        + (today.month - clients['start_date'].dt.month)
                    ) % 3 == 0
              )
        ]

        return clients_to_invoice_df


#
# Define a class that encapsulates the water table
class Water:
    def __init__(self):
        pass

    # Get current water readings for each water connection
    @staticmethod
    def get_current_readings() -> DataFrame:
        #
        # Get all water readings for each water connection
        # - Get all water connections
        # Execute query on database
        kasa.execute("select * from wconnection")
        #
        # Fetch and store the query result from database
        all_water_connections: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame from the result
        all_water_connections_df: DataFrame = DataFrame(all_water_connections)
        #
        # Filter dataframe to have only active water connections
        filter_date: date = date(9999, 12, 31)
        active_water_connections_df: DataFrame = all_water_connections_df[
            all_water_connections_df['end_date'] == filter_date]
        #
        # - Get all water meters
        # Execute query DB for all water meters
        kasa.execute("select * from wmeter")
        #
        # Fetch the returning result
        all_water_meters: list[dict] = kasa.fetchall()
        #
        # Create dataframe of water meters using Pandas
        water_meters_df: DataFrame = DataFrame(all_water_meters)
        #
        # - Get all water readings
        # Execute query DB for all water readings
        kasa.execute("select * from wreading")
        #
        # Fetch the returning result (i.e., a list of dictionaries|rows)
        all_water_readings: list[dict] = kasa.fetchall()
        #
        # Create dataframe of water readings using Pandas
        water_readings_df: DataFrame = DataFrame(all_water_readings)
        #
        # - Join dataframes for water connection, water meter, and water
        # reading tables
        #
        # Join the active water connections dataframe to the water
        # meters dataframe
        water_connections_and_meters_df: DataFrame = merge(
            active_water_connections_df, water_meters_df, on='wmeter',
            how='inner'
        )
        # Join the active water connections and water meters dataframe
        # to the water readings dataframe
        all_water_connection_readings: DataFrame = merge(
            water_connections_and_meters_df,
            water_readings_df,
            on='wmeter',
            how='inner'
        )
        # Get the current water reading for each water connection
        # - Get latest reading date for each water connection
        # Group dataframe by water connection
        grouped_water_connections_df: DataFrameGroupBy = (
            all_water_connection_readings.groupby('wconnection')
        )
        #
        # Get the row INDEX of the maximum water reading date for each water
        #   connection
        # Index - identifier|label for each row in a dataframe
        max_dates_indices: DataFrame = (
            grouped_water_connections_df['date'].idxmax()
        )
        #
        # Use .loc to get the rows that match the indices above
        latest_readings_df: DataFrame = all_water_connection_readings.loc[
            max_dates_indices]
        #
        # Filter columns to show
        latest_readings_df: DataFrame = latest_readings_df[
            ['wconnection', 'serial_no', 'rate', 'date', 'value']
        ]
        # Rename column names
        latest_readings_df: DataFrame = latest_readings_df.rename(
            columns={
                'date': 'curr_date',
                'value': 'curr_value'
            }
        )
        return latest_readings_df

    #
    # Define method to get previous (last invoiced) water readings for each
    #   water connection
    @staticmethod
    def get_previous_readings() -> DataFrame:
        #
        # Get the last invoice date
        # - Get last invoice period
        # Execute query on database
        kasa.execute("select * from period")
        #
        # Fetch the results from Database
        all_periods: list[dict] = kasa.fetchall()
        #
        # Create a Dataframe from the fetched result
        periods_df: DataFrame = DataFrame(all_periods)
        #
        # - Get today's date
        leo: datetime = datetime.today()
        #
        # Based on today's date (month), get the invoice period of last month
        last_period_df: DataFrame = periods_df[
            (periods_df['month'] == leo.month - 1)
            & (periods_df['year'] == leo.year)
            ]
        # - Get cutoff date based on the returned period (last period)
        cutoff_date: date = last_period_df.iloc[0]['cutoff']
        #
        # Get water readings based on the cutoff|last invoice date
        # Execute query on database
        kasa.execute("select * from water")
        #
        # Fetch the result of the query from database
        all_invoiced_water_readings: list[dict] = kasa.fetchall()
        #
        # Create a dataframe from the fetched result
        all_invoiced_water_readings_df: DataFrame = DataFrame(
            all_invoiced_water_readings
        )
        #
        # - Filter the dataframe to have only rows of the last invoice date
        # |cutoff date
        last_invoiced_water_readings_df: DataFrame = \
            all_invoiced_water_readings_df[
                all_invoiced_water_readings_df['curr_date'] == cutoff_date
            ]
        #
        # Filter the columns to be displayed
        last_invoiced_water_readings_df: DataFrame = (
            last_invoiced_water_readings_df[
                ['wconnection', 'curr_date', 'curr_value']
            ]
        )
        #
        # Rename the column names
        last_invoiced_water_readings_df: DataFrame = (
            last_invoiced_water_readings_df.rename(columns={
                'curr_date': 'prev_date',
                'curr_value': 'prev_value'
            }
            )
        )

        return last_invoiced_water_readings_df

    #
    # Define method that calculates the daily average consumption and
    #   total amount to invoice each water connection
    def get_calculations(self) -> DataFrame:
        #
        # Join the current readings and previous readings DataFrames
        curr_and_prev_rds: DataFrame = merge(
            self.get_previous_readings(),
            self.get_current_readings(),
            on='wconnection',
            how='inner'
        )
        #
        # Add column to calculate the number of days that water was consumed
        #   after the last reading for each water connection
        #
        # Change the current and previous dates to datetime types in Pandas so
        #   that we can perform arithmetics on them
        # - Convert previous date to Pandas standard datetime
        curr_and_prev_rds['prev_date'] = to_datetime(
            curr_and_prev_rds['prev_date'])
        #
        # - Convert current date to Pandas standard datetime
        curr_and_prev_rds['curr_date'] = to_datetime(
            curr_and_prev_rds['curr_date'])
        #
        # Subtract the previous date from the current date to get the number of
        #   days water was consumed
        # - Use the 'days' property to transform the return value from a
        #       Timedelta object to an integer
        curr_and_prev_rds['consumption_days'] = (
                curr_and_prev_rds['curr_date'] - curr_and_prev_rds['prev_date']
        ).dt.days
        #
        # Add column to calculate the total water consumption for each water
        #   connection
        curr_and_prev_rds['total_consumption'] = (
                curr_and_prev_rds['curr_value']
                - curr_and_prev_rds['prev_value']
        )
        #
        # Add column to calculate the average daily consumption for each water
        #   connection
        curr_and_prev_rds['avg_daily_cons'] = (
                curr_and_prev_rds['total_consumption'] / curr_and_prev_rds[
                    'consumption_days']
        )
        #
        # Add column to calculate the amount each water connection is supposed
        #   to be invoiced
        curr_and_prev_rds['amount'] = (
                curr_and_prev_rds['total_consumption'] *
                curr_and_prev_rds['rate']
        )
        # Reorder the columns
        curr_and_prev_rds: DataFrame = curr_and_prev_rds[
            ['wconnection', 'serial_no', 'prev_date', 'prev_value', 'curr_date',
             'curr_value', 'consumption_days', 'total_consumption',
             'avg_daily_cons', 'rate', 'amount']]

        return curr_and_prev_rds


#
# Define a class for service charges calculations
class Service(Client):
    def __init__(self):
        #
        # Call the constructor method of the parent class (Client class)
        super().__init__()
        #
        # Define the client DataFrame as a property
        self.client: DataFrame = super().get_clients_to_invoice()

    #
    # Get the subscriptions and service charges for each client
    def get_subscriptions(self) -> DataFrame:
        #
        # Get all subscriptions for each client
        # - Get the subscriptions
        kasa.execute("select client, subscription, service from subscription")
        subscriptions: list[dict] = kasa.fetchall()
        subscriptions_df = DataFrame(subscriptions)
        #
        # - Join the clients and Subscriptions DataFrames
        clients_subscriptions_df: DataFrame = merge(
            self.client, subscriptions_df, how="inner", on="client"
        )
        #
        # Get the services for each client
        # - Get the services
        kasa.execute("select service, name, price from service")
        services: list[dict] = kasa.fetchall()
        services_df = DataFrame(services)
        #
        # - Join the clients and subscriptions DataFrame to the services
        #       DataFrame
        clients_subscriptions_services_df: DataFrame = merge(
            clients_subscriptions_df, services_df, how="inner", on="service"
        )
        #
        # Calculate the total charges
        #
        # Group the DataFrame by client and get the total charges
        grouped_clients_services_dfgb: DataFrameGroupBy = (
            clients_subscriptions_services_df.groupby("client")
            .agg({'quarterly': "first", 'price': "sum"}))
        #
        # Convert the DataFrameGroupBy object to a DataFrame
        grouped_clients_services: DataFrame = (grouped_clients_services_dfgb
                                               .reset_index())
        #
        # If client is quartely then the price should be multiplied by 3
        grouped_clients_services.loc[
            grouped_clients_services["quarterly"] == 1, "price"] = \
            grouped_clients_services["price"] * 3

        return grouped_clients_services

    #
    # Get the services for each client


client = Service()
cl = client.get_subscriptions()
print("f")
