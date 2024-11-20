# File objective: Structure the 'wconnection_amount.py' file using a class
#
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
globalz = {
    'connection': konekshon,
    'cursor': kasa,
    'pd': pd,
    'DataFrame': DataFrame,
    'merge': merge,
    'date': date,
    'datetime': datetime
}


#
# 4. Define a class that encapsulates the water table
class Water:
    #
    # 4.1. Define the constructor method
    def __init__(self, global_variables):
        pass

    #
    # 4.2. Define the methods of the class
    # 4.2.1. Define method to get current water readings for each water
    #   connection
    def get_current_readings(self) -> DataFrame:
        #
        # 4.2.1.1. Execute query on database
        kasa.execute("select * from * wconnection")
        #
        # 4.2.1.2. Fetch and store the query result from database
        all_water_connections = kasa.fetchall()
        #
        # 4.2.1.3. Create a DataFrame from the result
        all_water_connections_df = DataFrame(all_water_connections)
        #
        # 4.2.1.4. Return the DataFrame
        return all_water_connections_df

    #
    # 4.2.2. Define method to get previous water readings for each water
    #   connection
    def get_previous_readings(self):
        return

    #
    # 4.2.3. Define method that calculates the daily average consumption and
    #   total amount to invoice each water connection
    def get_calculations(self):
        return


#
# 5. Instantiate the class
calculations_november = Water(globalz)
#
# 6. Call the calculation method to display|show the water table
water_calculations = calculations_november.get_current_readings()
print('f')
