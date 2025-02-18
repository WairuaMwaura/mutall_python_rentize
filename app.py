# File Objective:  in another file with static properties
#
# Import classes
from rentize import Rentize

rental = Rentize(11, 2024)
client = rental.client.get_active_clients()
subscribed_services = rental.service.get_subscribed_services()
auto_services = rental.service.get_auto_services()

print('f')
