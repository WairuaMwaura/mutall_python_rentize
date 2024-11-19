# Display wmeter table in Python
#
# Import mysql.connector library to interact with mysql database
import mysql.connector
#
# Import pandas library to display sql results in table format (dataframes) and
#   manipulate and analyze the data
import pandas as pd
#
# Set display options to show all columns
# None means no limit to the number of columns displayed
pd.set_option('display.max_columns', None)
#
# Prevents series (columns) wrapping to a new line
pd.set_option('display.expand_frame_repr', False)
#
# Store database connection configuration arguments as a dictionary
config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mutall_rental',
    }
#
# Connect to the database using the configs above
konekshon = mysql.connector.connect(
    host = config['host'],
    user = config['user'],
    password = config['password'],
    database = config['database']
)
#
# Create a cursor object
# A cursor is an object that allows you to interact with the database. It’s used
#   to execute SQL queries against the database and fetch results
# Set the connection.cursor property to return a list of dictionaries (i.e.,
#   [
#       {'wmeter': 3, 'serial_no': '15061026', 'name': 'Lovina', 'comment': None, 'is_supply': 0},
#       {'wmeter': 4, 'serial_no': '300746', 'name': 'Ukiristo', 'comment': None, 'is_supply': 0},
#       {'wmeter': 5, 'serial_no': '14081172', 'name': 'Kentagon', 'comment': None, 'is_supply': 0},...
#   ]
#   instead of the default, list of tuples (i.e., [('wmeter', ...), ('serial_no', ...),
#   ('value', ...),]
#   In a dictionary, each column name becomes a key, and its corresponding value
#       is the data for that column.
#    Each dictionary in the result set represents a single row of data retrieved
#       from a database table.
kasa = konekshon.cursor(dictionary=True)
#
# Display the wmeter table
# Use the cursor to run the query against the
#   database.
kasa.execute(
    """
        select
            * 
        from 
            wmeter
        where
            wmeter.comment not like 'closed'
             or wmeter.comment is null
    """
)
#
# Collect the above results into a list
# cursor.fetchall() method returns a list of dictionaries as set in the cursor
#   initialization
wmeter_table_data = kasa.fetchall()
#
# cursor.description property gives information about the columns of the above
#   result set. The information is in a list of dictionaries as set in the
#       initialization
# Pass the table data list as an argument to create a dataframe
wmeter_df = pd.DataFrame(wmeter_table_data)
#
# Print wmeter dataframe
print(wmeter_df)
