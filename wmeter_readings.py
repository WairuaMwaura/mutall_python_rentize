# Display wmeter and wreading tables in Python
#
def init():
    # Import libraries inside the function
    import mysql.connector
    import pandas as pd

    # Set display options for pandas
    pd.set_option('display.max_columns', None)
    pd.set_option('display.expand_frame_repr', False)

    # Store database connection configuration arguments as a dictionary
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'mutall_rental',
    }

    # Connect to the database using the configs above
    connection = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    #
    # Create a cursor object
    cursor = connection.cursor(dictionary=True)
    #
    # Return the connection, cursor, and pd objects in a tuple to use them
    #   outside the init function
    return connection, cursor, pd
#
# Call the init function
init_results = init()
#
# Access the connection, cursor, and pd by assigning the return values of init
#   to variables
connection = init_results[0]
cursor = init_results[1]
pd = init_results[2]
#
# Collect data from the wmeter table
cursor.execute(
    """
        select
            * 
        from 
            wmeter
    """
)
#
# Collect the above results into a list
wmeter_table_data = cursor.fetchall()
#
# Create dataframe for wmeter
wmeter_df = pd.DataFrame(wmeter_table_data)
#
# Filter wmeter dataframe to have only open wmeters (i.e., comment is None or
#   comment is not 'closed')
active_wmeter_df = wmeter_df[(wmeter_df['comment'].isna()) | (wmeter_df['comment'] != 'closed')]
#
# Collect data from the wreading table
cursor.execute(
    """
    select
        *
    from
        wreading
    """
)
#
# Collect the above results into a list
wreading_table_data = cursor.fetchall()
#
# Create dataframe for wreading
wreading_df = pd.DataFrame(wreading_table_data)
#
# Join the two dataframes and display the resulting dataframe
wmeter_wreading_inner_joined_df = pd.merge( wreading_df, active_wmeter_df, on = 'wmeter', how='inner')
print('')