# File objective 1: Structure the 'wconnection_amount.py' file using a class
# File objective 2: Define another class for getting the utility charges
#
# Import libraries to use
from mysql.connector import connect
from mysql.connector.cursor import MySQLCursorDict
import pandas as pd
from mysql.connector.pooling import PooledMySQLConnection
from pandas import DataFrame, merge, to_datetime, Timedelta
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
        # Get the row number and cutoff date and convert the latter to datetime format.
        row_number = current_period.iloc[0]["row_number"]
        self.curr_cutoff = pd.to_datetime(current_period.iloc[0]["cutoff"])
        #
        # Get the cutoff date of the period just before the current one.
        #
        # Get the previous period by subtracting 1 from the row_num of the
        #   current period.
        previous_period = period_df[period_df["row_number"] == row_number - 1]
        #
        # Get the cutoff (date) from the previous period and convert it to datetime format.
        self.prev_cutoff = pd.to_datetime(previous_period.iloc[0]["cutoff"])
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
        return active_client_df


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
        # 1. Get all active water connections and the clients they are connected
        #   to
        # Execute query on database to get all water connections
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
        # 2. Get all water meters
        # Execute query DB for all water meters
        kasa.execute("select * from wmeter")
        #
        # Fetch the returning result
        all_water_meters: list[dict] = kasa.fetchall()
        #
        # Create dataframe of water meters using Pandas
        water_meters_df: DataFrame = DataFrame(all_water_meters)
        #
        # 3. Get all water readings for each meter
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
        # 1. Join the active water connections dataframe to the water
        #   meters dataframe
        water_connections_and_meters_df: DataFrame = merge(
            active_water_connections_df, water_meters_df, on='wmeter',
            how='inner'
        )
        # 2. Join the active water connections and water meters dataframe
        #   to the water readings dataframe
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
        # Filter the readings to only include those for the specified month and
        #   year
        filtered_df = all_water_connection_readings[
            (all_water_connection_readings['date'].dt.month == self.client.month) &
            (all_water_connection_readings['date'].dt.year == self.client.year)
            ]
        #
        # Group the filtered data by water connection
        grouped_water_connections_df = filtered_df.groupby('wconnection')
        #
        # Get index of the latest reading (max date) for each water connection
        max_dates_indices = grouped_water_connections_df['date'].idxmax()
        #
        # Use .loc to get the rows that match those indices
        latest_readings_df = filtered_df.loc[max_dates_indices]
        #
        # Filter columns to show
        latest_readings_df: DataFrame = latest_readings_df[
            ['client_name', 'wconnection', 'serial_no', 'rate', 'date', 'value']
        ]
        #
        # Rename column names
        latest_readings_df: DataFrame = latest_readings_df.rename(
            columns={
                'date': 'curr_date',
                'value': 'curr_value'
            }
        )
        #
        # Truncate extra decimals from rate and curr_value columns
        latest_readings_df['rate'] = (latest_readings_df['rate']
                                      .astype(int))
        latest_readings_df['curr_value'] = (latest_readings_df['curr_value']
                                            .round(2))
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
    # Get the utility subscriptions charges for each client
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
        #
        # Get the actual price based on negotiated price or service price (i.e.,
        #   If the negotiated_price is missing (NaN), use the service_price
        #   instead and save that as a new column called actual_price)
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
             'connection_count', 'service_name', 'service_price',
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


#
# Define a class that encapsulates rent charges for each client
class Rent(Service):
    def __init__(self, client):
        super().__init__(client)

    #
    # Get the report period (i.e., the first day of the month| day after the
    #   cutoff period and the last day of the month or the cutoff period).
    def get_rental_charges(self):
        #
        # Get previous period cutoff based on variable date
        kasa.execute(
            """
                select
                    cutoff as previous_month_cutoff
                from
                    `period`
                where
                    `period`.`year` = %s
                    and `period`.`month` = %s
            """, (self.client.year, self.client.month - 1)
        )
        start_period: list[dict] = kasa.fetchall()
        start_period_df: DataFrame = DataFrame(start_period)
        #
        # Get the next day after the previous period cutoff
        start_period_df["previous_month_cutoff"] = to_datetime(
            start_period_df["previous_month_cutoff"]
            + Timedelta(days=1)
        )
        #
        # Rename the previous period cutoff to start period
        start_period_df: DataFrame = start_period_df.rename(
            columns={'previous_month_cutoff': 'start_period'}
        )
        #
        # get end period based on variable date
        kasa.execute(
            """
                select
                    cutoff as end_period
                from
                    `period`
                where
                    `period`.`year` = %s
                    and `period`.`month` = %s
            """, (self.client.year, self.client.month)
        )
        end_period: list[dict] = kasa.fetchall()
        end_period_df: DataFrame = DataFrame(end_period)
        #
        # calculate difference in years to get period phase (normal period,
        #   review period, renew period)
        # 1. Select all agreements for valid clients
        kasa.execute(
            """
            select
                agreement.agreement,
                agreement.client,
                agreement.room,
                agreement.start_date,
                agreement.duration,
                agreement.review,
                agreement.amount
            from
                agreement
            where
                agreement.terminated is null
            """
        )
        agreements: list[dict] = kasa.fetchall()
        agreements_df: DataFrame = DataFrame(agreements)
        valid_agreements_df: DataFrame = agreements_df.merge(
            self.client.get_active_clients(), on="client", how="right"
        )
        #
        # Add the start and end period columns
        valid_agreements_df: DataFrame = valid_agreements_df.merge(
            start_period_df, how="cross"
        )
        valid_agreements_df: DataFrame = valid_agreements_df.merge(
            end_period_df, how="cross"
        )
        #
        #
        # 2. Get the difference in years between the agreememnt start date and
        #   the start period date for the report
        #
        # Convert to datetime format
        valid_agreements_df['start_date'] = pd.to_datetime(valid_agreements_df['start_date'])
        valid_agreements_df['start_period'] = pd.to_datetime(valid_agreements_df['start_period'])
        valid_agreements_df["day_difference"] = (valid_agreements_df["start_period"]
                                                - valid_agreements_df["start_date"]
                                             ).dt.total_seconds() / (60 * 60 * 24)
        valid_agreements_df["year_diff"] = valid_agreements_df["day_difference"] / 365.25
        #
        # 3. Label each client based on the difference in years
        #
        # 3.1. If difference between agreement start date and start period is
        #   less than the review years then it is the normal period phase
        valid_agreements_df.loc[valid_agreements_df["year_diff"]
                                < valid_agreements_df["review"], "phase"] = "normal"
        #
        # 3.2. If difference between agreement start date and start period is
        #   less than or equal to the duration years and is greater or equal to
        #   the review years then it is the review period phase
        valid_agreements_df.loc[(valid_agreements_df["year_diff"]
                                >= valid_agreements_df["review"]) & (valid_agreements_df["year_diff"] <= valid_agreements_df["duration"]), "phase"] = "review"
        # 3.3. If difference between agreement start date and start period is
        # #   greater than the duration years then it is the renew period phase
        valid_agreements_df.loc[valid_agreements_df["year_diff"]
                                > valid_agreements_df["duration"], "phase"] = "renew"
        #
        # Calculate the rent for each tenant based on their period phase
        #
        # If client is in normal period phase then rent is as per agreement
        valid_agreements_df.loc[valid_agreements_df["phase"] == "normal", "rent_charge"] = valid_agreements_df["amount"] * valid_agreements_df["factor"]
        #
        # If client is in review period phase then rent is increased by 10%
        valid_agreements_df.loc[valid_agreements_df["phase"] == "review", "rent_charge"] = valid_agreements_df["amount"] * 1.1 * valid_agreements_df["factor"]
        #
        # If client is in renew period phase then rent is increased by 20%
        valid_agreements_df.loc[valid_agreements_df["phase"] == "renew", "rent_charge"] = valid_agreements_df["amount"] * 1.2 * valid_agreements_df["factor"]
        #
        # Remove null values and convert decimal values to integer
        valid_agreements_df['amount'] = valid_agreements_df['amount'].fillna(0).astype(int)
        valid_agreements_df["duration"] = valid_agreements_df["duration"].fillna(0).astype(int)
        valid_agreements_df["rent_charge"] = valid_agreements_df["rent_charge"].fillna(0).astype(int)
        #
        # Remove time from date values
        valid_agreements_df['start_date'] = to_datetime(valid_agreements_df['start_date']).dt.date
        valid_agreements_df['start_period'] = to_datetime(valid_agreements_df['start_period']).dt.date
        #
        # Filter and reorder columns to display
        filtered_valid_agreements_df: DataFrame = valid_agreements_df[
            ['year', 'month', 'client', 'room', 'client_name', 'agreement', 'amount',
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
        kasa.execute(
            """
            select
                *
            from
                ebill
            where
                year(ebill.due_date) = %s and
                month(ebill.due_date) = %s
            """, (self.client.year, self.client.month)
        )
        all_ebills: list[dict] = kasa.fetchall()
        all_ebills_df: DataFrame = DataFrame(all_ebills)
        #
        # Truncate current amount values to 2 decimal places
        all_ebills_df['current_amount'] = (all_ebills_df['current_amount']
                                                .map("{:.2f}".format))
        #
        # Filter columns to show.
        # all_ebills_df = all_ebills_df[[
        #
        # ]]

        return all_ebills_df

    #
    # Get bills for electricity meters that are connected to occupied rooms
    # (i.e., active clients).
    def get_client_ebills(self) -> DataFrame:
        kasa.execute(
            """
            select distinct
                    client.client,
                    emeter.emeter,
                    emeter.new_num_2023_03 as `emeter_no`,
                    eaccount.eaccount,
                    eaccount.num as `eaccount_no`
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
            on='eaccount'
        )
        #
        # Get distinct ebills for active clients
        active_clients_ebills_df = active_clients_ebills_df.drop_duplicates(subset=['ebill'])
        #
        # Filter columns to show
        active_clients_ebills_df = active_clients_ebills_df[[
            'client',
            'emeter_no',
            'eaccount_no',
            'ebill',
            'current_amount'
        ]]

        return active_clients_ebills_df

    #
    # Get ebills for electricity meters that are connected to rooms (whether
    # occupied or not).
    def get_room_ebills(self) -> DataFrame:
        kasa.execute(
            """
            select
                room.room,
                room.uid as `room_uid`,
                emeter.emeter,
                emeter.new_num_2023_03 as `emeter_no`,
                eaccount.eaccount,
                eaccount.num as `eaccount_no`
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
            on='eaccount'
        )
        #
        # Get the distinct ebills for the connected rooms.
        connected_rooms_bills_df = connected_rooms_bills_df.drop_duplicates(
            subset=['ebill'])
        #
        # Filter columns to show.
        connected_rooms_bills_df = connected_rooms_bills_df[[
            'room',
            'room_uid',
            'emeter',
            'emeter_no',
            'eaccount',
            'eaccount_no',
            'ebill',
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
        # 2. Keep only those ebills that didn't have a client column.
        unattended_bills_df = unattended_bills_df[unattended_bills_df["client"].isna()]
        unattended_bills_df = unattended_bills_df[[
            "room",
            "room_uid",
            "eaccount_no_x",
            "emeter_no_x",
            "ebill",
            "current_amount_x"
        ]]

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
        service_ebills_df = service_ebills_df[[
            "emeter",
            "eaccount_x",
            "ebill",
            "current_amount_x"
        ]]
        return service_ebills_df


#
# Define a class that encapsulates bank reconciliation
class Payment(Service):
    def __init__(self, client: Client):
        super().__init__(client)
        pass
