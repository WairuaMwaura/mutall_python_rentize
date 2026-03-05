#
# Import classes
from rentize import Client, Item, Service, Water, Charges, Rent, Electricity, Payment, Adjustment, Credit, Debit
#
# Date Variables
month = 6
year = 2019
#
# Instantiate the Client class with the specified date variables.
# Add factor/ quarterly rate for clients on active client class ????????????????????????????????????????
client = Client(month, year)
#
# Instantiate the Item class with the client object
item = Item(client)
#
# # Instantiate Service class
service = Service(client)
# #
# # List active clients
clients_df = client.get_active_clients()
# #
# # # Get current water readings based on the variable date at the top
# curr_water_rds = Water(client).get_current_readings()
# # #
# # # Get previous water readings based on the variable date at the top
# prev_water_rds = Water(client).get_previous_readings()
#
#
# Instantiate Charges class
# charges = Charges(client)
#
# Show subscribed charges for each client
# subs_df = charges.get_subscribed_charges()
#
# Show automatic charges for each client
# auto_charges_df = charges.get_auto_charges()
# # Instantiate Rent class
# rent = Rent(client)
# rent_p = rent.get_rental_charges()
#
# # Use the current client to create an instance of the Electricity class.
# e_class = Electricity(client)
# #
# # Use the electric instance to get the electricity readings of the specified month.
# all_ebills = e_class.get_all_bills()
# client_ebills = e_class.get_client_ebills()
# room_bills = e_class.get_room_ebills()
# unattended_ebills = e_class.get_unattended_ebills()
# service_ebills = e_class.get_service_ebills()
#
# Instantiate the payment class with the item object
payment = Payment(client)
curr_payments = payment.get_payments()
#
# Instantiate Adjustment class
# adjustment = Adjustment(client)
#
# Instamtiate Credit class
credit = Credit(client)
credit_payments = credit.get_credit()
#
# Instantiate Debit class
debit = Debit(client)
debit_payments = debit.get_debit()
print('finished')
