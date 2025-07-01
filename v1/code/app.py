# File Objective:  in another file with static properties
#
# Import classes
from rentize import Rentize
#
# Instantiate the Rentize Class
rental = Rentize(11, 2024)
#
# List active clients and their number of water connections
client = rental.client.get_active_clients()
#
# List subscribed services for each active client
subscribed_charges = rental.charges.get_subscribed_charges()
#
# List all automatic services for each active client
auto_charges = rental.charges.get_auto_charges()

print('check debugger variables to view DataFrames')
