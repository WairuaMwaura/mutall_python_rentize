# Display wreading table in Python
#
# Import mysql.connector library to interact with mysql database
import mysql.connector
#
# Import pandas library for data manipulation and analysis
import pandas as pd
#
# Set display options to show all columns
pd.set_option('display.max_columns', None)
#
# Prevents columns wrapping to a new line
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
connection = mysql.connector.connect(
    host = config['host'],
    user = config['user'],
    password = config['password'],
    database = config['database']
)
#
# Create a cursor object
cursor = connection.cursor(dictionary=True)
#
# Collect data from the wreading table
cursor.execute("select * from wreading")
#
# Collect the above results into a list
wreading_table_data = cursor.fetchall()
#
# Create dataframe for wreading
wreading_df = pd.DataFrame(wreading_table_data)
#
# Print wmeter dataframe
print(wreading_df)