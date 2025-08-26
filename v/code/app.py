#
# Import classes
from rentize import Client, Service, Water, Charges, Rent, Electricity
#
# Date Variables
month = 5
year = 2025
#
# Instantiate Client class
client = Client(month, year)
# #
# # Instantiate Service class
# service = Service(client)
# #
# # List active clients
# clients_df = service.client.get_active_clients()
# #
# # Instantiate Charges class
# charges = Charges(client)
# #
# # Show subscribed charges for each client
# subs_df = charges.get_subscribed_charges()
# #
# # Show automatic charges for each client
# auto_charges_df = charges.get_auto_charges()
# #
# # Get current water readings based on the variable date at the top
# curr_water_rds = Water(client).get_current_readings()
# #
# # Get previous water readings based on the variable date at the top
# prev_water_rds = Water(client).get_previous_readings()
# #
# # Instantiate Rent class
# rent = Rent(client)
# rent_p = rent.get_rental_charges()

elect = Electricity(client)
# prev_elec_rds = elect.get_previous_readings()
curr_elec_rds = elect.get_current_readings()



print('finished')
