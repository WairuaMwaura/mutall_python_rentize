# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the utility charges
#
# Import libraries to use
from mysql.connector import connect
import pandas as pd
from pandas import DataFrame, merge, to_datetime, Timedelta
from datetime import date, datetime
from contextlib import contextmanager

#
# Set display options for pandas - to show all columns and full width
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
#
# Connect to the database
#
# 1. Store database connection configuration arguments in a dictionary
db_config: dict[str, str] = {
    'host': 'localhost',
    'user': 'mutall',
    'password': 'mutall@2023',
    'database': 'mutallco_rental',
}


#
# 2. Create a context manager (to help me use `with` statements) to manage the
#   opening and closing of the connection and cursor objects
@contextmanager
def connection_and_cursor_manager():
    #
    # Setup
    conn = connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    #
    # Give control back to the `with` block
    try:
        yield conn, cursor
    #
    # Clean up
    finally:
        cursor.close()
        conn.close()


#
# Define a class that encapsulates all the clients to be invoiced this month
class Client:
    #
    # Define the constructor method
    def __init__(self, month, year):
        self.month: int = month
        self.year: int = year
        self.curr_cutoff: datetime | None = None
        self.prev_cutoff: datetime | None = None
        self.client = self.get_active_clients()

    # Define the methods of the class
    #
    # Get list of all active clients and their respective payment modes from the
    #   database.
    # Define method that gets active clients
    def get_active_clients(self) -> DataFrame:
        #
        # Execute query to select period data from the database
        with connection_and_cursor_manager() as (kon, kasa):
            kasa.execute(
                """
                select
                    *
                from
                    `period`;
                """
            )
            #
            # Fetch results from the database
            period: list[dict] = kasa.fetchall()
            #
            # Create a DataFrame for the fetched result
            period_df: DataFrame = DataFrame(period)
            #
            # Create a numbered list of all periods so we can easily find "previous"
            #   periods.
            period_df["row_number"] = range(len(period_df))
            #
            # Get the row number and cutoff date for the current reporting period.
            current_period = period_df[
                (period_df["month"] == self.month) & (period_df["year"] == self.year)
            ]
            #
            # Throw an error if there is no period for that month.
            if current_period.empty:
                raise ValueError("No matching period found for that month in the database")
            #
            # Get the row number of current period (will use it to get the previous period)
            row_number = current_period.iloc[0]["row_number"]
            #
            # Get current cutoff date and convert it to datetime.datetime object format.
            self.curr_cutoff = pd.to_datetime(current_period.iloc[0]["cutoff"]).to_pydatetime()
            #
            # Get the cutoff date of the previous period (based on the current period above).
            #
            # Get the previous period by subtracting 1 from the row_num of the
            #   current period.
            previous_period = period_df[period_df["row_number"] == row_number - 1]
            #
            # Get the cutoff (date) from the previous period and convert it to datetime format.
            self.prev_cutoff = pd.to_datetime(previous_period.iloc[0]["cutoff"]).to_pydatetime()
            #
            # Prepare agreements:
            #   - Impute null values on the 'terminated' column as "end date" (9999-12-31)
            #       for agreements that are still active (no termination date).
            #   - Keep only agreements marked as valid.
            kasa.execute(
                """
                select
                    *
                from
                    agreement
                where
                    valid = 1;
                """
            )
            valid_agreements: list[dict] = kasa.fetchall()
            valid_agreement_df: DataFrame = DataFrame(valid_agreements)
            #
            # Impute null terminated date values with End of time date as end_date.
            #
            # Get End of time as datetime format.
            # Since pandas datetime64[ns] can only handle dates between 1677-09-21 and 2262-04-11.
            e_o_t = pd.Timestamp("2262-04-11")
            # Convert start dates and end dates to datetime formart
            valid_agreement_df["start_date"] = pd.to_datetime(valid_agreement_df["start_date"])
            valid_agreement_df["end_date"] = pd.to_datetime(
                valid_agreement_df["terminated"].fillna(e_o_t)
            )
            #
            # Link each valid agreement above with a client getting the earliest start date
            #   and the latest end date.
            # Get all Clients.
            kasa.execute("select * from client;")
            client_df = DataFrame(kasa.fetchall())
            client_tenure_df = (
                #
                # Join client and valid_agreements dataframes.
                valid_agreement_df.merge(client_df, on="client", how="inner")
                #
                # Group by client when performing the aggregate functions (i.e., min
                #   and max).
                .groupby("client", as_index=False).agg(
                    name=("name", "first"),
                    title=("title", "first"),
                    start_date=("start_date", "min"),
                    end_date=("end_date", "max")
                )
            )
            #
            # Get the clients who were active during the specified reporting period:
            #   An active client is one whose agreement started on or before the current
            #       cutoff and their agreement ended after the previous cutoff.
            active_client_df = client_tenure_df[
                (client_tenure_df["start_date"] <= self.curr_cutoff)
                & (client_tenure_df["end_date"] > self.prev_cutoff)
                ]
            #
            # Add month and year columns
            active_client_df["month"] = self.month
            active_client_df["year"] = self.year
            return active_client_df


#
# Define a class that encapsulates invoice for each client
class Invoice:
    def __init__(self, client: Client):
        self.opening_balance: int | None = None
        self.electricity: int | None = None
        self.client = client


#
# Define an Item classs that encapsulates all individual items.
# How to show relationship with Invoice class?????????????????????????????????????????????
class Item():
    def __init__(self, client: Client):
        self.name: str | None = None
        self.amount: int | None = None
        self.client = client

    #
    # Create an abstract method that  list individual items e.g., payments, or
    #   services separately.


#
# Define a Service class that encapsulates all utilities
class Service(Item):
    def __init__(self, client):
        self.quantity: int | None = None
        self.rate: int | None = None
        self.amount: int | None = None
        super().__init__(client)

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

    #
    # Get current water readings for each water connection
    def get_current_readings(self) -> DataFrame:
        """
        Get current water readings for each water connection.
        Returns the latest reading on or before the current cutoff date.
        """
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all water connections with their associated clients
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
            # Rename 'start_date' and 'end_date' columns for the water
            #   connection to avoid conflicts with 'start_date' and 'end_date'
            #   columns for agreement.
            clients_water_connections_df: DataFrame = clients_water_connections_df.rename(
                columns={
                    'start_date_x': 'connection_start_date',
                    'end_date_x': 'connection_end_date'
                }
            )
            #
            # Filter dataframe to have only active water connections
            filter_date: date = date(9999, 12, 31)
            active_water_connections_df: DataFrame = \
            clients_water_connections_df[
                clients_water_connections_df[
                    'connection_end_date'] == filter_date
                ]
            #
            # Get all water meters
            kasa.execute("select * from wmeter")
            all_water_meters: list[dict] = kasa.fetchall()
            water_meters_df: DataFrame = DataFrame(all_water_meters)
            #
            # Get all water readings
            kasa.execute("select * from wreading")
            all_water_readings: list[dict] = kasa.fetchall()
            water_readings_df: DataFrame = DataFrame(all_water_readings)
            #
            # Join active water connections to water meters
            water_connections_and_meters_df: DataFrame = merge(
                active_water_connections_df, water_meters_df, on='wmeter',
                how='inner'
            )
            #
            # Join to water readings
            all_water_connection_readings: DataFrame = merge(
                water_connections_and_meters_df,
                water_readings_df,
                on='wmeter',
                how='inner'
            )
            #
            # Convert date to datetime for comparison
            all_water_connection_readings['date'] = pd.to_datetime(
                all_water_connection_readings['date']
            )
            #
            # Filter readings to only include those on or before current cutoff
            filtered_df = all_water_connection_readings[
                all_water_connection_readings['date'] <= self.client.curr_cutoff
                ]
            #
            # Check if filtered_df is empty
            if filtered_df.empty:
                # Return empty DataFrame with expected columns
                return DataFrame(columns=[
                    'client', 'name', 'wconnection', 'serial_no',
                    'rate', 'curr_date', 'curr_value'
                ])
            #
            # Group by water connection and get the index of max date
            grouped_water_connections_df = filtered_df.groupby('wconnection')
            max_dates_indices = grouped_water_connections_df['date'].idxmax()
            #
            # Use .loc to get the rows that match those indices
            latest_readings_df = filtered_df.loc[max_dates_indices]
            #
            # Filter columns to show
            latest_readings_df: DataFrame = latest_readings_df[
                ['client', 'name_x', 'wconnection', 'serial_no', 'rate', 'date',
                 'value']
            ]
            #
            # Rename column names
            latest_readings_df: DataFrame = latest_readings_df.rename(
                columns={
                    'name_x': 'name',
                    'date': 'curr_date',
                    'value': 'curr_value'
                }
            )
            #
            # Truncate extra decimals from rate and curr_value columns
            latest_readings_df['rate'] = latest_readings_df['rate'].astype(int)
            latest_readings_df['curr_value'] = latest_readings_df[
                'curr_value'].round(2)

            return latest_readings_df


    #
    # Define method to get previous (last invoiced) water readings for each
    #   water connection
    def get_previous_readings(self) -> DataFrame:
        """
        Get previous water readings for each water connection.
        Returns the latest reading on or before the previous cutoff date.
        """
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all water connections with their associated clients
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
            # Rename 'start_date' and 'end_date' columns for the water
            #   connection to avoid conflicts with 'start_date' and 'end_date'
            #   columns for agreement.
            clients_water_connections_df: DataFrame = clients_water_connections_df.rename(
                columns={
                    'start_date_x': 'connection_start_date',
                    'end_date_x': 'connection_end_date'
                }
            )
            #
            # Filter dataframe to have only active water connections
            filter_date: date = date(9999, 12, 31)
            active_water_connections_df: DataFrame = \
            clients_water_connections_df[
                clients_water_connections_df[
                    'connection_end_date'] == filter_date
                ]
            #
            # Get all water meters
            kasa.execute("select * from wmeter")
            all_water_meters: list[dict] = kasa.fetchall()
            water_meters_df: DataFrame = DataFrame(all_water_meters)
            #
            # Get all water readings
            kasa.execute("select * from wreading")
            all_water_readings: list[dict] = kasa.fetchall()
            water_readings_df: DataFrame = DataFrame(all_water_readings)
            #
            # Join active water connections to water meters
            water_connections_and_meters_df: DataFrame = merge(
                active_water_connections_df, water_meters_df, on='wmeter',
                how='inner'
            )
            #
            # Join to water readings
            all_water_connection_readings: DataFrame = merge(
                water_connections_and_meters_df,
                water_readings_df,
                on='wmeter',
                how='inner'
            )
            #
            # Convert date to datetime for comparison
            all_water_connection_readings['date'] = pd.to_datetime(
                all_water_connection_readings['date']
            )
            #
            # Filter readings to only include those on or before previous cutoff
            filtered_df = all_water_connection_readings[
                all_water_connection_readings['date'] <= self.client.prev_cutoff
                ]
            #
            # Check if filtered_df is empty
            if filtered_df.empty:
                # Return empty DataFrame with expected columns
                return DataFrame(columns=[
                    'client', 'name', 'wconnection', 'prev_date', 'prev_value'
                ])
            #
            # Group by water connection and get the index of max date
            grouped_water_connections_df = filtered_df.groupby('wconnection')
            max_dates_indices = grouped_water_connections_df['date'].idxmax()
            #
            # Use .loc to get the rows that match those indices
            latest_readings_df = filtered_df.loc[max_dates_indices]
            #
            # Filter columns to show
            latest_readings_df: DataFrame = latest_readings_df[
                ['client', 'name_x', 'wconnection', 'date', 'value']
            ]
            #
            # Rename column names
            latest_readings_df: DataFrame = latest_readings_df.rename(
                columns={
                    'name_x': 'name',
                    'date': 'prev_date',
                    'value': 'prev_value'
                }
            )
            #
            # Truncate extra decimals from prev_value column
            latest_readings_df['prev_value'] = latest_readings_df[
                'prev_value'].round(2)

            return latest_readings_df

    #
    # Define method to calculate the Water charges for each client
    def calculate_water_charges(self) -> DataFrame:
        """
        Calculate water charges for each client based on consumption.
        Amount = (Current Reading - Previous Reading) × Rate
        """
        #
        # Get current and previous readings
        curr_readings = self.get_current_readings()
        prev_readings = self.get_previous_readings()
        #
        # Merge current and previous readings
        # Use left merge so all current readings are kept
        water_df = curr_readings.merge(
            prev_readings[['client', 'wconnection', 'prev_value']],
            on=['client', 'wconnection'],
            how='left'
        )
        #
        # Fill missing previous values with 0 (for new connections or no previous readings)
        water_df['prev_value'] = water_df['prev_value'].fillna(0)
        #
        # Calculate consumption (current - previous)
        water_df['consumption'] = water_df['curr_value'] - water_df['prev_value']
        #
        # Calculate water amount (consumption × rate)
        water_df['amount'] = water_df['consumption'] * water_df['rate']
        #
        # Round amount to 2 decimal places
        water_df['amount'] = water_df['amount'].round(2)
        #
        # Reorder columns for better readability
        water_df = water_df[[
            'client',
            'name',
            'wconnection',
            'serial_no',
            'prev_value',
            'curr_value',
            'consumption',
            'rate',
            'amount'
        ]]
        return water_df


#
# Define a class that encapsulates utility charges calculations for each client
class Charges(Service):
    def __init__(self, client):
        #
        # Call the constructor method of the parent class (Service class)
        super().__init__(client)

    #
    # Get the utility subscriptions charges for each client
    def get_subscribed_charges(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all subscriptions for each client
            kasa.execute("select * from subscription")
            subs: list[dict] = kasa.fetchall()
            subs_df: DataFrame = DataFrame(subs)
            #
            # Add water connection feature/column to client class so that
            #   clients that have a water connection shouldn't be charged water
            #   service
            # 1. Select rooms rented by active clients.
            kasa.execute(
                """
                select
                    agreement.client,
                    room.room
                from
                    agreement
                    inner join room on agreement.room = room.room
                where
                    agreement.terminated is null and
                    agreement.valid = 1;
                """
            )
            rooms: list[dict] = kasa.fetchall()
            rooms_df: DataFrame = DataFrame(rooms)
            client_rooms_df = self.client.get_active_clients().merge(
                rooms_df, on="client", how="inner"
            )
            #
            # Remove duplicate columns.
            #
            # drop all _y columns
            client_rooms_df = client_rooms_df.loc[
                              :, ~client_rooms_df.columns.str.endswith('_y')]
            #
            # clean column names
            client_rooms_df.columns = client_rooms_df.columns.str.replace(
                '_x', '', regex=False
            )
            #
            # 2. Get water connection status for those rooms.
            kasa.execute(
                """
                select
                    wconnection.room,
                    wconnection.wconnection
                from
                    wconnection
                where
                    wconnection.disconnected is null and
                    wconnection.end_date = "9999-12.31"
                """
            )
            connected_rooms: list[dict] = kasa.fetchall()
            connected_rooms_df: DataFrame = DataFrame(connected_rooms)
            #
            # 3. Get the connection count for each client connected to water.
            #
            # 3.1. Merge the active client rooms with the water connection
            #   status.
            client_connections_df = (
                client_rooms_df.merge(connected_rooms_df, on="room", how="left")
            )
            #
            # 3.2. Get the connection count for each client
            client_connections_df = (
                client_connections_df
                .groupby("client")["wconnection"]
                .count()
                .reset_index(name="connection_count")
            )
            #
            # - Join the clients to Subscriptions DataFrame
            clients_subs_df: DataFrame = (
                client_connections_df
                .merge(subs_df, on="client", how="left")
            )
            #
            # Get the subscribed utility name and price for each client
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
            # Rename column names in DataFrame (i.e., amount column in subscription
            #   table is the negotiated price of the utility)
            clients_services_df = clients_services_df.rename(
                columns={
                    'name': 'service_name',
                    'price': 'service_price',
                    'amount': 'negotiated_price'
                }
            )
            # #
            # Get the actual price based on negotiated price or service price (i.e.,
            #   If the negotiated_price is missing (NaN), use the service_price
            #   instead and save that as a new column called actual_price)
            clients_services_df['actual_price'] = clients_services_df['negotiated_price'].fillna(clients_services_df['service_price'])
            #
            # If client is connected to water then the water service charge is zero
            clients_services_df.loc[
                (clients_services_df["service_name"] == "water")
                & (clients_services_df["connection_count"] > 0), "actual_price"
            ] = 0
            return clients_services_df
            # #
            # # Add calculated amount column for each client's subscribed service
            # clients_services_df['calculated_amount'] = (
            #         clients_services_df['actual_price']
            #         * clients_services_df['factor']
            # )
            # #
            # # Reorder columns in DataFrame
            # clients_services_df = clients_services_df[
            #     ['year', 'month', 'client', 'client_name', 'quarterly', 'factor',
            #      'connection_count', 'service_name', 'service_price',
            #      'negotiated_price', 'calculated_amount']
            # ]
            # #
            # # Replace NaN values with default value of zero and remove decimals from
            # #   service price, negotiated price, and calculated amount columns
            # clients_services_df['service_price'] = clients_services_df[
            #     'service_price'
            # ].fillna(0).astype(int)
            # clients_services_df['calculated_amount'] = clients_services_df[
            #     'calculated_amount'
            # ].fillna(0).astype(int)
            # clients_services_df['negotiated_price'] = clients_services_df[
            #     'negotiated_price'
            # ].fillna(0).astype(int)
            # return clients_services_df

    #
    # Get all services that are automatically charged
    def get_auto_charges(self):
        with connection_and_cursor_manager() as (kon, kasa):
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
            # Rename "name" for client and "name" for service columns to avoid
            #   conflicts.
            auto_clients_charges_df = auto_clients_charges_df.rename(
                columns={
                    'name_x': 'name',
                    'name_y': 'service_name'
                }
            )
            #
            # Get clients who appear in previous water readings and count their
            #   connections — clients NOT in previous readings get a count of 0.
            water = Water(self.client)
            prev_readings_df = water.get_previous_readings()
            #
            # Count connections per client from previous readings
            connection_counts: DataFrame = (
                prev_readings_df
                .groupby('client')['wconnection']
                .count()
                .reset_index()
                .rename(columns={'wconnection': 'connection_count'})
            )
            #
            # Left merge so ALL clients are kept; unmatched ones get NaN → fill with 0
            auto_clients_charges_df = auto_clients_charges_df.merge(
                connection_counts, on='client', how='left'
            )
            auto_clients_charges_df['connection_count'] = (
                auto_clients_charges_df['connection_count'].fillna(0).astype(
                    int)
            )
            #
            # If client is connected to water then the water service charge is
            #   zero
            auto_clients_charges_df.loc[
                (auto_clients_charges_df["service_name"] == "water")
                & (auto_clients_charges_df["connection_count"] > 0), "service_price"
            ] = 0
            #
            # Get factor for each client from Rent class
            rent = Rent(self.client)
            factors_df: DataFrame = (
                rent.get_rental_charges()[['client', 'factor']]
                .drop_duplicates(subset=['client'])
            )
            #
            # Merge factor into auto_clients_charges_df
            auto_clients_charges_df = auto_clients_charges_df.merge(
                factors_df, on='client', how='left'
            )
            #
            # Add calculated amount column for each client's subscribed service
            auto_clients_charges_df['calculated_amount'] = (
                    auto_clients_charges_df['actual_price']
                    * auto_clients_charges_df['factor']
            )
            #
            # Reorder columns in DataFrame
            auto_clients_charges_df = auto_clients_charges_df[
                ['year', 'month', 'client', 'name', 'factor',
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


#
# Define a class that encapsulates rent charges for each client
class Rent(Service):
    def __init__(self, client):
        super().__init__(client)

    #
    # Get the report period (i.e., the first day of the month | day after the
    #   previous cutoff period and the last day of the month or the current
    #   cutoff period).
    # Update the get_rental_charges method in the Rent class

    def get_rental_charges(self):
        """
        Calculate rental charges for each client.
        Uses cutoff dates already calculated in Client class.
        """
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Use the previous cutoff date (already calculated in Client class)
            # Add 1 day to get the start of the current period
            start_period = self.client.prev_cutoff + Timedelta(days=1)
            #
            # Use the current cutoff date (already calculated in Client class)
            # This is the end of the current period
            end_period = self.client.curr_cutoff
            #
            # Select all agreements for valid clients
            kasa.execute(
                """
                select
                    agreement.agreement,
                    agreement.client,
                    agreement.room,
                    agreement.start_date,
                    agreement.duration,
                    agreement.review,
                    agreement.amount,
                    client.quarterly
                from
                    agreement
                    inner join client on agreement.client = client.client
                where
                    agreement.terminated is null
                """
            )
            agreements: list[dict] = kasa.fetchall()
            agreements_df: DataFrame = DataFrame(agreements)
            #
            # Merge active clients with their agreements
            valid_agreements_df: DataFrame = agreements_df.merge(
                self.client.get_active_clients(), on="client", how="right"
            )
            #
            # Rename "name" column for client
            valid_agreements_df = valid_agreements_df.rename(
                columns={'name': 'client_name'})
            #
            # Convert start_date to datetime FIRST (must be before month_difference calculation)
            valid_agreements_df['start_date_x'] = pd.to_datetime(
                valid_agreements_df['start_date_x'])
            #
            # Calculate month difference between agreement start date and current period
            valid_agreements_df['month_difference'] = (
                    ((self.client.year - valid_agreements_df[
                        'start_date_x'].dt.year) * 12)
                    + (self.client.month
                       - valid_agreements_df['start_date_x'].dt.month)
            )
            #
            # Monthly clients have a factor of 1
            valid_agreements_df['factor'] = 1
            #
            # Quarterly clients that are due have a factor of 3
            valid_agreements_df.loc[
                (valid_agreements_df['quarterly'] == 1)
                & (valid_agreements_df['month_difference'] % 3 == 0),
                'factor'
            ] = 3
            #
            # Quarterly clients that are not due have a factor of 0
            valid_agreements_df.loc[
                (valid_agreements_df['quarterly'] == 1)
                & (valid_agreements_df['month_difference'] % 3 != 0),
                'factor'
            ] = 0
            #
            # Add the start and end period columns (using cutoff dates from Client class)
            valid_agreements_df['start_period'] = start_period
            valid_agreements_df['end_period'] = end_period
            #
            # Get the difference in years between the agreement start date and
            # the start period date for the report
            #
            # Convert to datetime format
            valid_agreements_df['start_date'] = pd.to_datetime(
                valid_agreements_df['start_date_x'])
            valid_agreements_df['start_period'] = pd.to_datetime(
                valid_agreements_df['start_period'])
            valid_agreements_df["day_difference"] = (valid_agreements_df[
                                                         "start_period"]
                                                     - valid_agreements_df[
                                                         "start_date"]
                                                     ).dt.total_seconds() / (
                                                                60 * 60 * 24)
            valid_agreements_df["year_diff"] = valid_agreements_df[
                                                   "day_difference"] / 365.25
            #
            # Label each client based on the difference in years
            #
            # If difference between agreement start date and start period is
            # less than the review years then it is the normal period phase
            valid_agreements_df.loc[valid_agreements_df["year_diff"]
                                    < valid_agreements_df[
                                        "review"], "phase"] = "normal"
            #
            # If difference between agreement start date and start period is
            # less than or equal to the duration years and is greater or equal to
            # the review years then it is the review period phase
            valid_agreements_df.loc[(valid_agreements_df["year_diff"]
                                     >= valid_agreements_df["review"]) & (
                                                valid_agreements_df[
                                                    "year_diff"] <=
                                                valid_agreements_df[
                                                    "duration"]), "phase"] = "review"
            #
            # If difference between agreement start date and start period is
            # greater than the duration years then it is the renew period phase
            valid_agreements_df.loc[valid_agreements_df["year_diff"]
                                    > valid_agreements_df[
                                        "duration"], "phase"] = "renew"
            #
            # Calculate the rent for each tenant based on their period phase
            #
            # If client is in normal period phase then rent is as per agreement
            valid_agreements_df.loc[
                valid_agreements_df["phase"] == "normal", "rent_charge"] = \
            valid_agreements_df["amount"] * valid_agreements_df["factor"]
            #
            # If client is in review period phase then rent is increased by 10%
            valid_agreements_df.loc[
                valid_agreements_df["phase"] == "review", "rent_charge"] = \
            valid_agreements_df["amount"] * 1.1 * valid_agreements_df["factor"]
            #
            # If client is in renew period phase then rent is increased by 20%
            valid_agreements_df.loc[
                valid_agreements_df["phase"] == "renew", "rent_charge"] = \
            valid_agreements_df["amount"] * 1.2 * valid_agreements_df["factor"]
            #
            # Remove null values and convert decimal values to integer
            valid_agreements_df['amount'] = valid_agreements_df[
                'amount'].fillna(0).astype(int)
            valid_agreements_df["duration"] = valid_agreements_df[
                "duration"].fillna(0).astype(int)
            valid_agreements_df["rent_charge"] = valid_agreements_df[
                "rent_charge"].fillna(0).astype(int)
            #
            # Remove time from date values
            valid_agreements_df['start_date'] = to_datetime(
                valid_agreements_df['start_date']).dt.date
            valid_agreements_df['start_period'] = to_datetime(
                valid_agreements_df['start_period']).dt.date
            valid_agreements_df['end_period'] = to_datetime(
                valid_agreements_df['end_period']).dt.date
            #
            # Filter and reorder columns to display
            filtered_valid_agreements_df: DataFrame = valid_agreements_df[
                ['year', 'month', 'client', 'room', 'client_name', 'agreement',
                 'amount',
                 'quarterly', 'start_date', 'duration', 'review', 'factor',
                 'start_period', 'end_period', 'phase', 'rent_charge']
            ]
            return filtered_valid_agreements_df


#
# Define a class that encapsulates electricity charges for each client
#
class Electricity(Service):
    def __init__(self, client: Client):
        super().__init__(client)

    #
    # Get bills for all electricity meters.
    def get_all_bills(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            kasa.execute(
                """
                select 
                    ebill.ebill,
                    eaccount.num as `eaccount_num`,
                    emeter.new_num_2023_03 as `emeter_num`,
                    ebill.due_date,
                    ebill.current_amount    
                from
                    ebill
                    inner join eaccount on ebill.eaccount = eaccount.eaccount
                    inner join elink on elink.eaccount = eaccount.eaccount
                    inner join emeter on elink.emeter = emeter.emeter
                where
                    ebill.due_date > %s and
                    ebill.due_date <= %s and
                    elink.end_date = "9999-12-31"
                order by
                    ebill.ebill
                """, (self.client.prev_cutoff, self.client.curr_cutoff)
            )
            #
            # Get column names
            columns = []
            #
            # After executing a SQL query, the cursor object  has a .description
            # attribute that contains metadata about the columns in the result
            # set. It's a tuple of 7-element tuples, one for each column:
            if kasa.description:
                #
                # Loop through the tuple
                for desc in kasa.description:
                    #
                    # Append the first element (i.e., column name) in each tuple
                    columns.append(desc[0])

            # Fetch results
            all_ebills: list[dict] = kasa.fetchall()
            #
            # Create DataFrame with columns even if empty
            all_ebills_df: DataFrame = DataFrame(all_ebills, columns=columns)
            #
            # Truncate current amount values to 2 decimal places
            all_ebills_df['current_amount'] = (all_ebills_df['current_amount']
                                                    .map("{:.2f}".format))

            return all_ebills_df

    #
    # Get bills for electricity meters that are connected to occupied rooms
    # (i.e., active clients).
    def get_client_ebills(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            kasa.execute(
                """
                select distinct
                        client.client,
                        client.name as `client_name`,
                        emeter.emeter,
                        emeter.new_num_2023_03 as `emeter_num`,
                        eaccount.eaccount,
                        eaccount.num as `eaccount_num`
                    from
                        eaccount
                        inner join elink on elink.eaccount = eaccount.eaccount
                        inner join emeter on elink.emeter = emeter.emeter
                        inner join econnection on econnection.emeter = emeter.emeter
                        inner join room on econnection.room = room.room
                        inner join agreement on agreement.room = room.room
                        inner join client on agreement.client = client.client
                """
            )
            client_eaccounts: list[dict] = kasa.fetchall()
            client_eaccounts_df: DataFrame = DataFrame(
                client_eaccounts)
            #
            # Get ebills for active clients
            #
            # Join client_eaccounts with active clients and all ebills.
            active_clients_ebills_df = client_eaccounts_df.merge(
                self.client.get_active_clients(),
                on="client",
                how="inner"
            ).merge(
                self.get_all_bills(),
                on='eaccount_num'
            )
            #
            # Remove duplicate columns.
            #
            # drop all _y columns
            active_clients_ebills_df = active_clients_ebills_df.loc[
                                       :, ~active_clients_ebills_df.columns.str.endswith('_y')]
            #
            # clean column names
            active_clients_ebills_df.columns = active_clients_ebills_df.columns.str.replace('_x', '', regex=False)
            #
            # Get distinct ebills for active clients
            active_clients_ebills_df = active_clients_ebills_df.drop_duplicates(subset=['ebill'])
            #
            # Filter columns to show
            active_clients_ebills_df = active_clients_ebills_df[[
                'ebill',
                'client_name',
                'eaccount_num',
                'emeter_num',
                'due_date',
                'current_amount'
            ]]
            #
            # Sort by ebill
            active_clients_ebills_df = active_clients_ebills_df.sort_values(
                by='ebill'
            )

            return active_clients_ebills_df

    #
    # Get ebills for electricity meters that are connected to rooms (whether
    # occupied or not).
    def get_room_ebills(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            kasa.execute(
                """
                select
                    room.room,
                    room.title as `room_title`,
                    room.uid as `room_uid`,
                    emeter.emeter,
                    emeter.new_num_2023_03 as `emeter_num`,
                    eaccount.eaccount,
                    eaccount.num as `eaccount_num`
                from
                    eaccount
                    inner join elink on elink.eaccount = eaccount.eaccount
                    inner join emeter on elink.emeter = emeter.emeter
                    inner join econnection on econnection.emeter = emeter.emeter
                    inner join room on econnection.room = room.room
                """
            )
            connected_rooms: list[dict] = kasa.fetchall()
            connected_rooms_df: DataFrame = DataFrame(
                connected_rooms)
            #
            # Get the ebills connected to a room.
            connected_rooms_bills_df = connected_rooms_df.merge(
                self.get_all_bills(),
                on='eaccount_num'
            )
            #
            # Get the distinct ebills for the connected rooms.
            connected_rooms_bills_df = connected_rooms_bills_df.drop_duplicates(
                subset=['ebill'])
            #
            # Remove duplicate columns.
            #
            # drop all _y columns
            connected_rooms_bills_df = connected_rooms_bills_df.loc[:,
                                       ~connected_rooms_bills_df.columns.str.endswith(
                                           '_y')]
            #
            # clean column names
            connected_rooms_bills_df.columns = connected_rooms_bills_df.columns.str.replace(
                '_x', '', regex=False)
            #
            # Filter columns to show.
            connected_rooms_bills_df = connected_rooms_bills_df[[
                'room',
                'room_uid',
                'room_title',
                'emeter',
                'emeter_num',
                'eaccount',
                'eaccount_num',
                'ebill',
                'due_date',
                'current_amount'
            ]]

            return connected_rooms_bills_df
    #
    # Get bills for electricity meters that are connected to unoccupied rooms.
    def get_unattended_ebills(self) -> DataFrame:
        #
        # 1. Perform a left join of the active client ebills against all
        # the rooms that have ebills.
        unattended_bills_df = self.get_room_ebills().merge(
            self.get_client_ebills(),
            on='ebill',
            how='left'
        )
        #
        # Remove duplicate columns.
        #
        # drop all _y columns
        unattended_bills_df = unattended_bills_df.loc[:,
                                   ~unattended_bills_df.columns.str.endswith(
                                       '_y')]
        #
        # clean column names
        unattended_bills_df.columns = unattended_bills_df.columns.str.replace(
            '_x', '', regex=False)
        #
        # 2. Keep only those ebills that didn't have a client column.
        unattended_bills_df = unattended_bills_df[unattended_bills_df["client_name"].isna()]
        unattended_bills_df = unattended_bills_df[[
            "ebill",
            "room_uid",
            "room_title",
            "eaccount_num",
            "emeter_num",
            "due_date",
            "current_amount"
        ]]
        #
        # Sort by ebill
        unattended_bills_df = unattended_bills_df.sort_values(
            by='ebill'
        )

        return unattended_bills_df

    #
    # Get bills for electricity meters that are not connected to rooms by:
    # 1. Left joining all ebills against ebills that are connected to rooms
    def get_service_ebills(self) -> DataFrame:
        service_ebills_df = self.get_all_bills().merge(
            self.get_room_ebills(),
            on='ebill',
            how='left'
        )
        #
        # 2. Keep only those where occupied room ebills didn't match.
        service_ebills_df = \
        service_ebills_df[service_ebills_df["room"].isna()]
        #
        # Remove duplicate columns.
        #
        # drop all _y columns
        service_ebills_df = service_ebills_df.loc[:,
                              ~service_ebills_df.columns.str.endswith(
                                  '_y')]
        #
        # clean column names
        service_ebills_df.columns = service_ebills_df.columns.str.replace(
            '_x', '', regex=False)
        service_ebills_df = service_ebills_df[[
            "ebill",
            "eaccount_num",
            "emeter_num",
            "due_date",
            "current_amount"
        ]]
        #
        # Sort by ebill
        service_ebills_df = service_ebills_df.sort_values(
            by='ebill'
        )

        return service_ebills_df


#
# Define a class that encapsulates bank reconciliation
class Payment(Item):
    def __init__(self, client):
        super().__init__(client)

    def get_payments(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all payments for current month
            kasa.execute(
                """
                select 
                    client.name,
                    payment.date,
                    payment.ref,
                    payment.description,
                    payment.amount
                from 
                    client
                    inner join payment on payment.client = client.client
                where
                    payment.date > %s and 
                    payment.date <= %s
                """, (self.client.prev_cutoff, self.client.curr_cutoff)
            )
            #
            # Fetch and store the query result from database
            current_payments: list[dict] = kasa.fetchall()
            #
            # Create a DataFrame from the result
            current_payments_df: DataFrame = DataFrame(current_payments)
            #
            # Truncate decimal places
            current_payments_df['amount'] = current_payments_df['amount'].astype(int)

            return current_payments_df


#
# Define a class that encapsulates opening balance
class Opening_Balance(Item):
    def __init__(self, client):
        super().__init__(client)
    #
    # Get opening balance
    def get_previous_opening_balance(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all closing balances for current month
            kasa.execute(
                """
                SELECT
                    client.client,
                    client.name,
                    invoice.invoice,
                    period.period,
                    period.cutoff,
                    closing_balance.amount
                FROM
                    client
                    inner join invoice on invoice.client = client.client
                    inner join period on invoice.period = period.period
                    inner join closing_balance on closing_balance.invoice = invoice.invoice
                where
                    period.cutoff > %s and
                    period.cutoff <= %s
                """, (self.client.prev_cutoff, self.client.curr_cutoff)
            )
            #
            # Fetch and store the query result from database
            opening_balance: list[dict] = kasa.fetchall()
            #
            # Create a DataFrame from the result
            opening_balance_df: DataFrame = DataFrame(opening_balance)
            #
            # Truncate decimal places
            opening_balance_df['amount'] = opening_balance_df['amount'].astype(int)

            return opening_balance_df
    #
    # Calculate opening Balance for next month
    def calculate_opening_balance(self) -> DataFrame:
        """
           Calculate current opening balance using the formula:
           O₀ = O₁ + W₁ - P₁ - C₁ + D₁ + R₀ + S₀

           Where:
           O₁ = Previous opening balance (from previous period's closing balance)
           W₁ = Water charges (current period)
           P₁ = Payments (current period)
           C₁ = Credits (current period)
           D₁ = Debits (current period)
           R₀ = Rent (current period)
           S₀ = Service charges (current period)

            UNION structure:

            client | service | amount

            Grouped by service (Opening, Rent, Water, etc.)
        """

        # ---------------------------
        # Opening Balance
        # ---------------------------
        opening_txn = (
            self.get_previous_opening_balance()[['client', 'amount']]
            .groupby('client', as_index=False)
            .sum()
        )
        opening_txn['service'] = 'Opening'

        # ---------------------------
        # Rent
        # ---------------------------
        rent = Rent(self.client)
        rent_df = rent.get_rental_charges()

        rent_txn = (
            rent_df.groupby('client')['rent_charge']
            .sum()
            .reset_index()
            .rename(columns={'rent_charge': 'amount'})
        )
        rent_txn['service'] = 'Rent'

        # ---------------------------
        # Water
        # ---------------------------
        water = Water(self.client)
        water_txn = (
            water.calculate_water_charges()
            .groupby('client')['amount']
            .sum()
            .reset_index()
        )
        water_txn['service'] = 'Water'

        # ---------------------------
        # Service Charges
        # ---------------------------
        charges = Charges(self.client)

        auto_txn = (
            charges.get_auto_charges()
            .groupby('client')['calculated_amount']
            .sum()
            .reset_index()
            .rename(columns={'calculated_amount': 'amount'})
        )

        sub_df = charges.get_subscribed_charges()
        factors = rent_df[['client', 'factor']].drop_duplicates()

        sub_txn = (
            sub_df
            .merge(factors, on='client', how='left')
            .assign(amount=lambda x: x['actual_price'] * x['factor'])
            .groupby('client')['amount']
            .sum()
            .reset_index()
        )

        service_txn = (
            auto_txn.merge(sub_txn, on='client', how='outer', suffixes=('_auto', '_sub'))
            .fillna(0)
        )

        service_txn['amount'] = service_txn['amount_auto'] + service_txn['amount_sub']
        service_txn = service_txn[['client', 'amount']]
        service_txn['service'] = 'Service_Charges'

        # ---------------------------
        # Electricity
        # ---------------------------
        electricity = Electricity(self.client)
        client_map = self.client.get_active_clients()[['client', 'name', 'title']]

        electricity_txn = (
            electricity.get_client_ebills()
            .assign(current_amount=lambda x: x['current_amount'].astype(float))
            .groupby('client_name')['current_amount']
            .sum()
            .reset_index()
            .rename(columns={'client_name': 'name', 'current_amount': 'amount'})
            .merge(client_map, on='name', how='left')
            [['client', 'amount']]
        )
        electricity_txn['service'] = 'Electricity'

        # ---------------------------
        # Payments (negative)
        # ---------------------------
        payment = Payment(self.client)

        payment_txn = (
            payment.get_payments()
            .groupby('name')['amount']
            .sum()
            .reset_index()
            .merge(client_map, on='name', how='left')
            [['client', 'amount']]
        )
        payment_txn['amount'] = -payment_txn['amount']
        payment_txn['service'] = 'Payment'

        # ---------------------------
        # Credit (negative)
        # ---------------------------
        credit = Credit(self.client)

        credit_txn = (
            credit.get_credit()
            .groupby('name')['amount']
            .sum()
            .reset_index()
            .merge(client_map, on='name', how='left')
            [['client', 'amount']]
        )
        credit_txn['amount'] = -credit_txn['amount']
        credit_txn['service'] = 'Credit'

        # ---------------------------
        # Debit (positive)
        # ---------------------------
        debit = Debit(self.client)

        debit_txn = (
            debit.get_debit()
            .groupby('client')['amount']
            .sum()
            .reset_index()
            .merge(client_map, on='client', how='left')
            [['client', 'amount']]
        )
        debit_txn['service'] = 'Debit'

        # ---------------------------
        # UNION
        # ---------------------------
        all_txns = pd.concat([
            opening_txn,
            rent_txn,
            water_txn,
            service_txn,
            electricity_txn,
            payment_txn,
            credit_txn,
            debit_txn
        ], ignore_index=True)

        # ---------------------------
        # Final cleanup
        # ---------------------------
        all_txns['amount'] = all_txns['amount'].fillna(0).astype(int)

        service_order = [
            'Opening',
            'Rent',
            'Water',
            'Service_Charges',
            'Electricity',
            'Payment',
            'Credit',
            'Debit'
        ]

        all_txns['service'] = pd.Categorical(
            all_txns['service'],
            categories=service_order,
            ordered=True
        )

        all_txns = all_txns.sort_values(['service', 'client']).reset_index(drop=True)
        #
        # Tabulate the data horizontally
        # Use 'client' as index to group transactions per client
        # pivoted_txns = all_txns.pivot_table(
        #     index='client',
        #     columns='service',
        #     values='amount',
        #     fill_value=0,
        #     aggfunc='sum'
        # )
        #
        # Use cross tab to pivot the DataFrame
        pivoted_txns = pd.crosstab(
            index=all_txns['client'],  # rows
            columns=all_txns['service'],  # columns
            values=all_txns['amount'],  # values to aggregate
            aggfunc='sum'  # aggregation
        )
        #
        # Get Subtotal for all amounts.
        pivoted_txns["Closing_Balance"] = pivoted_txns[['Opening', 'Payment', 'Rent',
            'Service_Charges', 'Water', 'Electricity', 'Credit', 'Debit']].sum(axis=1)
        #
        # Impute NaN values with zero
        pivoted_txns = pivoted_txns.fillna(0).astype(int)
        #
        # Remove the client as index
        pivoted_txns = pivoted_txns.reset_index()
        #
        # Add client name and title to DataFrame
        pivoted_txns = pivoted_txns.merge(
            client_map,
            on='client',
            how='left'
        )
        #
        # Reorder columns
        pivoted_txns = pivoted_txns[[
            'client', 'name', 'title', 'Opening', 'Payment', 'Rent',
            'Service_Charges', 'Water', 'Electricity', 'Credit', 'Debit',
            'Closing_Balance'
        ]]


        return pivoted_txns


#
# Define a class that encapsulates invoice adjustments
class Adjustment(Item):
    def __init__(self, client):
        super().__init__(client)



#
# Define a class that encapsulates debit for each client
class Credit(Adjustment):
    def __init__(self, client):
        super().__init__(client)

    def get_credit(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all payments for current month
            kasa.execute(
                """
                select 
                    client.name,
                    credit.date,
                    credit.amount,
                    credit.reason
                from 
                    client
                    inner join credit on credit.client = client.client
                where
                    credit.date > %s and
                    credit.date <= %s
                """, (self.client.prev_cutoff, self.client.curr_cutoff)
            )
            #
            # Fetch and store the query result from database
            credit: list[dict] = kasa.fetchall()
            #
            # Create a DataFrame from the result
            credit_df: DataFrame = DataFrame(credit)
            #
            # Truncate decimal places
            credit_df['amount'] = credit_df['amount'].astype(int)

            return credit_df


#
# Define a class that encapsulates debit for each client
class Debit(Adjustment):
    def __init__(self, client):
        super().__init__(client)

    def get_debit(self) -> DataFrame:
        with connection_and_cursor_manager() as (kon, kasa):
            #
            # Get all payments for current month
            kasa.execute(
                """
                select
                    client.client, 
                    client.name,
                    debit.date,
                    debit.amount,
                    debit.reason
                from 
                    client
                    inner join debit on debit.client = client.client
                where
                    debit.date > %s and
                    debit.date <= %s
                """, (self.client.prev_cutoff, self.client.curr_cutoff)
            )
            #
            # Fetch and store the query result from database
            debit: list[dict] = kasa.fetchall()
            #
            # Force schema: Even if there is no data, the listed columns must exist.
            debit_df = DataFrame(debit, columns=[
                'client',
                'name',
                'date',
                'amount',
                'reason'
            ])
            #
            # Reduce to needed fields before aggregation
            debit_df = DataFrame(debit, columns=['client', 'amount'])

            # Aggregate debits
            debit_df = (
                debit_df
                .groupby('client')['amount']
                .sum()
                .reset_index()
            )

            # Get ALL active clients
            clients_df = self.client.get_active_clients()[['client']]

            # Left join → ensures every client appears
            debit_df = clients_df.merge(debit_df, on='client', how='left')

            # Fill missing with 0
            debit_df['amount'] = debit_df['amount'].fillna(0).astype(int)

            return debit_df
