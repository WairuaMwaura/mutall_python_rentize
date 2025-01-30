# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the service charges
#
# Import libraries to use
from mysql.connector import connect
from mysql.connector.cursor import MySQLCursorDict
import pandas as pd
from mysql.connector.pooling import PooledMySQLConnection
from pandas import DataFrame, merge, to_datetime
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
def init() -> tuple[PooledMySQLConnection, MySQLCursorDict]:
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
    conn: PooledMySQLConnection = connect(**config)
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
# Manage other classes
class Rentize:
    def __init__(self, month, year):
        self.month = month
        self.year = year
        self.client = Client(month, year)
        self.service = Service(month, year)

    #
    # Define method for showing all active clients
    def show_client(self):
        return self.client.get_active_clients()

    #
    # Define method for showing all services charged
    def show_service(self):
        return self.service.get_subscriptions()

    #
    # Define method for showing all auto services
    def show_auto_service(self):
        return self.service.get_auto_services()


#
# Define a class that encapsulates all the clients to be invoiced this month
class Client:
    #
    # Define the constructor method
    def __init__(self, month, year):
        self.month = month
        self.year = year
        self.specified_date = datetime(self.year, self.month, 1)

    # Define the methods of the class
    #
    # Define method that gets active clients
    def get_active_clients(self) -> DataFrame:
        #
        # Get list of all clients that have a valid agreement and their
        #   respective payment modes from the database.
        #
        # Execute query on the database
        kasa.execute(
            """
            with
                valid_agreement as (
                    select distinct
                        client,
                        #
                        # Select the first start_date for client with multiple
                        #  agreement start dates
                        min(start_date) as start_date
                    from
                        agreement
                    where
                        valid = 1
                        and `terminated` is null
                    group by
                        client
                )
            select
                client.client,
                client.name as client_name,
                client.quarterly,
                valid_agreement.start_date
            from
                client
                inner join valid_agreement on valid_agreement.client = client.client
            """
        )
        #
        # Fetch results from the database
        active_clients: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame for the fetched result
        active_clients_df: DataFrame = DataFrame(active_clients)
        #
        # Convert agreement start date to standard date format
        active_clients_df['start_date'] = to_datetime(
            active_clients_df['start_date']
        )
        #
        # Add year and month columns in DataFrame
        active_clients_df['year'] = self.year
        active_clients_df['month'] = self.month
        #
        # Calculate factor for each client based on the specified date
        #
        # Calculate month difference for each client between their agreement
        #   first date and the specified date
        active_clients_df['month_difference'] = (
            ((self.specified_date.year - active_clients_df['start_date'].dt.year)*12)
            + (self.specified_date.month - active_clients_df['start_date'].dt.month)
        )
        #
        # Calculate factor for each client based on their payment type
        #
        # Monthly clients have a factor of 1
        active_clients_df['factor'] = 1
        #
        # Quarterly clients that are due have a factor of 3
        active_clients_df.loc[
            (active_clients_df['quarterly'] == 1)
            & (active_clients_df['month_difference'] % 3 == 0),
            'factor'
        ] = 3
        active_clients_df.loc[
            (active_clients_df['quarterly'] == 1)
            & (active_clients_df['month_difference'] % 3 != 0),
            'factor'
        ] = 0

        return active_clients_df


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
        # Handle month and year for the last period and have condition for
        #   current date being January
        last_month = leo.month - 1 if leo.month > 1 else 12
        year = leo.year if leo.month > 1 else leo.year - 1
        #
        # Get the invoice period of last month
        last_period_df: DataFrame = periods_df[
            (periods_df['month'] == last_month) & (periods_df['year'] == year)
        ]
        # Get cutoff date based on the returned period (last period)
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
        # |cutoff date for each wconnection
        last_invoiced_water_readings_df: DataFrame = \
            all_invoiced_water_readings_df[
                all_invoiced_water_readings_df['curr_date'] == cutoff_date
            ]
        print(last_invoiced_water_readings_df.head())
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
            last_invoiced_water_readings_df.rename(
                columns={
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
        #
        # Add room for each

        return curr_and_prev_rds


#
# Define a class for service charges calculations for each client
class Service(Client):
    def __init__(self, month, year):
        #
        # Call the constructor method of the parent class (Client class)
        super().__init__(month, year)
        #
        # Define the client DataFrame as a property
        self.client: DataFrame = super().get_active_clients()

    #
    # Get the subscriptions and service charges for each client
    def get_subscriptions(self) -> DataFrame:
        #
        # Get all subscriptions for each client
        kasa.execute("select client, subscription, service from subscription")
        subs: list[dict] = kasa.fetchall()
        subs_df: DataFrame = DataFrame(subs)
        #
        # - Join the clients to invoice and Subscriptions DataFrames
        clients_subs_df: DataFrame = merge(
            self.client, subs_df, how="inner", on="client"
        )
        #
        # Get the services for each client
        # - Get the services
        kasa.execute("select service, name, price from service")
        services: list[dict] = kasa.fetchall()
        services_df: DataFrame = DataFrame(services)
        #
        # - Join the clients and subscriptions DataFrame to the services
        #       DataFrame
        clients_services_df: DataFrame = merge(
            clients_subs_df, services_df, how="inner", on="service"
        )
        #
        # Rename column names in DataFrame
        clients_services_df = clients_services_df.rename(
            columns={
                'name': 'service_name',
                'price': 'service_price',
            }
        )
        #
        # Add amount column for each client service
        clients_services_df['amount'] = (
                clients_services_df['service_price']
                * clients_services_df['factor']
        )
        #
        # Reorder columns in DataFrame
        clients_services_df = clients_services_df[[
            'year', 'month', 'client', 'client_name', 'quarterly',
            'service_name', 'service_price', 'factor', 'amount'
        ]]
        #
        # Replace NaN values with default value of zero and remove decimals from
        #   service price and amount columns
        clients_services_df['service_price'] = clients_services_df[
            'service_price'
        ].fillna(0).astype(int)
        clients_services_df['amount'] = clients_services_df[
            'amount'
        ].fillna(0).astype(int)

        return clients_services_df

    #
    # Get all services that are automatically charged
    def get_auto_services(self):
        kasa.execute("select * from service where auto = 1")
        auto_services: list[dict] = kasa.fetchall()
        auto_services_df: DataFrame = DataFrame(auto_services)
        #
        # Merge the Client DataFrame to the automatic services DataFrame
        auto_clients_df: DataFrame = merge(
            self.client,
            auto_services_df,
            how='cross'
        )
        #
        # Rename column names in DataFrame
        auto_clients_df = auto_clients_df.rename(
            columns={
                'name': 'service_name',
                'price': 'service_price',
            }
        )
        #
        # Add amount column for each client auto service
        auto_clients_df['amount'] = (
                auto_clients_df['service_price']
                * auto_clients_df['factor']
        )
        #
        # Reorder columns in DataFrame
        auto_clients_df = auto_clients_df[[
            'year', 'month', 'client', 'client_name', 'quarterly',
            'service_name',
            'service_price', 'factor', 'amount'
        ]]
        #
        # Replace NaN values with default value of zero and remove decimals from
        #   service price and amount columns
        auto_clients_df['service_price'] = auto_clients_df[
            'service_price'
        ].fillna(0).astype(int)
        auto_clients_df['amount'] = auto_clients_df[
            'amount'
        ].fillna(0).astype(int)

        return auto_clients_df
