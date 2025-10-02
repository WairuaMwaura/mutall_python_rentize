# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the utility charges
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
# Define a class that encapsulates all the clients to be invoiced this month
class Client:
    #
    # Define the constructor method
    def __init__(self, month, year):
        self.month: int = month
        self.year: int = year
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
                #
                # Select all valid agreements
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
                ),
                #
                # Select all clients with valid agreements
                valid_clients as (
                    select
                        client.client,
                        client.name as client_name,
                        client.quarterly,
                        valid_agreement.start_date
                    from
                        client
                        inner join valid_agreement on valid_agreement.client = client.client
                ),
                #
                # all rooms with water connection
                connected_rooms as (
                    select
                        wconnection.wconnection,
                        room.room
                    from
                        wconnection
                        left join room on wconnection.room = room.room
                ),
                #
                # all clients with water connection
                connected_clients as (
                    select
                        connected_rooms.*,
                        agreement.client,
                        agreement.terminated,
                        agreement.valid,
                        agreement.start_date
                    from
                        connected_rooms
                        left join agreement on agreement.room = connected_rooms.room
                ),
                #
                # all valid clients with or without water connection
                        valid_connected_clients as (
                            select
                                valid_clients.*,
                                connected_clients.wconnection
                            from
                                valid_clients
                                left join connected_clients on connected_clients.client = valid_clients.client
                )
                #
                # show number of water connections for each client
                select 
                    client, 
                    client_name, 
                    quarterly, 
                    start_date, 
                    count(wconnection) AS connection_count
                from
                    valid_connected_clients
                group by
                    client, client_name, quarterly, start_date;
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
        #
        # Filter DataFrame columns to show
        active_clients_df: DataFrame = active_clients_df[
            ['year', 'month', 'client', 'client_name', 'quarterly', 'factor',
             'connection_count']
        ]

        return active_clients_df


#
# Define a Service class that encapsulates all utilities
class Service:
    def __init__(self, client: Client):
        self.quantity: int | None = None
        self.rate: int | None = None
        self.amount: int | None = None
        self.client = client

    def calculate_amount(self):
        if self.quantity is not None and self.rate is not None:
            self.amount = self.quantity * self.rate
        else:
            print("⚠️ Quantity or rate is None. Cannot calculate amount.")
#
# Define a class that encapsulates water calculations for each client
class Water(Service):
    def __init__(self, client):
        super().__init__(client)

    # Get current water readings for each water connection
    def get_current_readings(self) -> DataFrame:
        #
        # Get all water readings for each water connection
        # - Get all water connections
        # Execute query on database
        kasa.execute(
            """
                select
                    wconnection.*,
                    room.uid,
                    agreement.client 
                from 
                    wconnection
                    inner join room on wconnection.room = room.room
                    inner join agreement on agreement.room = room.room
            """
        )
        #
        # Fetch and store the query result from database
        connected_clients: list[dict] = kasa.fetchall()
        #
        # Create a DataFrame from the result
        connected_clients_df: DataFrame = DataFrame(connected_clients)
        #
        # Merge active clients from Client class
        clients_water_connections_df: DataFrame = connected_clients_df.merge(
            self.client.get_active_clients(), on="client", how="inner"
        )
        #
        # Filter dataframe to have only active water connections
        filter_date: date = date(9999, 12, 31)
        active_water_connections_df: DataFrame = clients_water_connections_df[
            clients_water_connections_df['end_date'] == filter_date]
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
        # - Join dataframes for active water connection, water meter, and water
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
        #
        # Convert date for all water connections readings to datetime
        all_water_connection_readings['date'] = pd.to_datetime(
            all_water_connection_readings['date']
        )
        # Filter the readings to only include those for the specified month and year
        filtered_df = all_water_connection_readings[
            (all_water_connection_readings['date'].dt.month == self.client.month) &
            (all_water_connection_readings['date'].dt.year == self.client.year)
            ]

        # Group the filtered data by water connection
        grouped_water_connections_df = filtered_df.groupby('wconnection')

        # Get index of the latest reading (max date) for each water connection
        max_dates_indices = grouped_water_connections_df['date'].idxmax()

        # Use .loc to get the rows that match those indices
        latest_readings_df = filtered_df.loc[max_dates_indices]
        #
        # Filter columns to show
        latest_readings_df: DataFrame = latest_readings_df[
            ['client_name', 'wconnection', 'serial_no', 'rate', 'date', 'value']
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
    def get_previous_readings(self) -> DataFrame:
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
        last_month = self.client.month - 1 if self.client.month > 1 else 12
        year = self.client.year if self.client.month > 1 else self.client.year - 1
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
        kasa.execute(
            """
                select
                    water.*,
                    invoice.client
                from
                    water
                    inner join invoice on water.invoice = invoice.invoice
            """
        )
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
        #
        # Merge with last invoiced water readings active clients water
        #   connections Dataframes
        active_invoiced_water_readings_df: DataFrame = last_invoiced_water_readings_df.merge(
            self.client.get_active_clients(), on="client", how="inner"
        )
        #
        # Filter the columns to be displayed
        active_invoiced_water_readings_df: DataFrame = (
            active_invoiced_water_readings_df[
                ['client_name', 'wconnection', 'curr_date', 'curr_value']
            ]
        )
        #
        # Rename the column names
        active_invoiced_water_readings_df: DataFrame = (
            active_invoiced_water_readings_df.rename(
                columns={
                    'curr_date': 'prev_date',
                    'curr_value': 'prev_value'
                }
            )
        )

        return active_invoiced_water_readings_df



#
# Define a class that encapsulates utility charges calculations for each client
class Charges(Service):
    def __init__(self, client):
        #
        # Call the constructor method of the parent class (Service class)
        super().__init__(client)
    #
    # Get the subscriptions and utility charges for each client
    def get_subscribed_charges(self) -> DataFrame:
        #
        # Get all subscriptions for each client
        kasa.execute("select * from subscription")
        subs: list[dict] = kasa.fetchall()
        subs_df: DataFrame = DataFrame(subs)
        #
        # - Join the clients to Subscriptions DataFrame
        clients_subs_df: DataFrame = self.client.get_active_clients().merge(
            subs_df, on="client", how="left"
        )

        #
        # Get the subscribed services for each client
        # - Get the services
        kasa.execute("select * from service")
        services: list[dict] = kasa.fetchall()
        services_df: DataFrame = DataFrame(services)
        #
        # - Join the clients and subscriptions DataFrame to the services
        #       DataFrame
        clients_services_df: DataFrame = clients_subs_df.merge(
            services_df, how="left", on="service"
        )
        #
        # Rename column names in DataFrame
        clients_services_df = clients_services_df.rename(
            columns={
                'name': 'service_name',
                'price': 'service_price',
                'amount': 'negotiated_price'
            }
        )
        #
        # Get the actual price based on negotiated price or service price
        clients_services_df['actual_price'] = clients_services_df['negotiated_price'].fillna(clients_services_df['service_price'])
        #
        # If client is connected to water then the water service charge is zero
        clients_services_df.loc[
            (clients_services_df["service_name"] == "water")
            & (clients_services_df["connection_count"] > 0), "service_price"
        ] = 0
        #
        # Add calculated amount column for each client's subscribed service
        clients_services_df['calculated_amount'] = (
                clients_services_df['actual_price']
                * clients_services_df['factor']
        )
        #
        # Reorder columns in DataFrame
        clients_services_df = clients_services_df[
            ['year', 'month', 'client', 'client_name', 'quarterly', 'factor',
            'connection_count','service_name', 'service_price',
             'negotiated_price', 'calculated_amount']
        ]
        #
        # Replace NaN values with default value of zero and remove decimals from
        #   service price, negotiated price, and calculated amount columns
        clients_services_df['service_price'] = clients_services_df[
            'service_price'
        ].fillna(0).astype(int)
        clients_services_df['calculated_amount'] = clients_services_df[
            'calculated_amount'
        ].fillna(0).astype(int)
        clients_services_df['negotiated_price'] = clients_services_df[
            'negotiated_price'
        ].fillna(0).astype(int)
        return clients_services_df

    #
    # Get all services that are automatically charged
    def get_auto_charges(self):
        kasa.execute("select * from service where auto = 1")
        auto_charges: list[dict] = kasa.fetchall()
        auto_charges_df: DataFrame = DataFrame(auto_charges)
        #
        # Merge the Client DataFrame to the automatic services DataFrame
        auto_clients_df: DataFrame = merge(
            self.client.get_active_clients(),
            auto_charges_df,
            how='cross'
        )
        #
        # Merge client and service DataFrame to Subscription DataFrame
        kasa.execute("select * from subscription")
        subs: list[dict] = kasa.fetchall()
        subs_df: DataFrame = DataFrame(subs)
        #
        # - Join the clients and subscriptions DataFrame to the services
        #       DataFrame
        auto_clients_charges_df: DataFrame = auto_clients_df.merge(
            subs_df, how="left", on="client"
        )
        #
        # Remove duplicates
        auto_clients_charges_df = auto_clients_charges_df.drop_duplicates(
            subset=["client", "service_x"])
        #
        # Rename column names in DataFrame
        auto_clients_charges_df = auto_clients_charges_df.rename(
            columns={
                'name': 'service_name',
                'price': 'service_price',
                'amount': 'negotiated_price'
            }
        )
        #
        # Get the actual price based on negotiated price or service price
        auto_clients_charges_df['actual_price'] = auto_clients_charges_df[
            'negotiated_price'].fillna(auto_clients_charges_df['service_price'])
        #
        # If client is connected to water then the water service charge is zero
        auto_clients_charges_df.loc[
            (auto_clients_charges_df["service_name"] == "water")
            & (auto_clients_charges_df["connection_count"] > 0), "service_price"
        ] = 0
        #
        # Add calculated amount column for each client's subscribed service
        auto_clients_charges_df['calculated_amount'] = (
                auto_clients_charges_df['actual_price']
                * auto_clients_charges_df['factor']
        )
        #
        # Reorder columns in DataFrame
        auto_clients_charges_df = auto_clients_charges_df[
            ['year', 'month', 'client', 'client_name', 'quarterly', 'factor',
             'connection_count', 'service_name', 'service_price',
             'negotiated_price', 'calculated_amount']
        ]
        #
        # Replace NaN values with default value of zero and remove decimals from
        #   service price, negotiated price, and calculated amount columns
        auto_clients_charges_df['service_price'] = auto_clients_charges_df[
            'service_price'
        ].fillna(0).astype(int)
        auto_clients_charges_df['calculated_amount'] = auto_clients_charges_df[
            'calculated_amount'
        ].fillna(0).astype(int)
        auto_clients_charges_df['negotiated_price'] = auto_clients_charges_df[
            'negotiated_price'
        ].fillna(0).astype(int)
        return auto_clients_charges_df