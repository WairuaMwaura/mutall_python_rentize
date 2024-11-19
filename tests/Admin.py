# File objective: Create a class that extends another class
#
# Import the class 'User' to extend it
from user import User
#
# Extend the imported class


class Admin(User):
    #
    # Define constructor method for the child class
    def __init__(self, username, email, password):
        #
        # Call the constructor method of the parent class
        super().__init__(username, email, password)

    #
    # Define a method only accessible to the Admin class
    def add_user(self):
        return f"Hey {self.username.title()}, you have successfully added the user!"

    #
    # Define a class method - depends on the class
    @classmethod
    def remove_user(cls):
        return "Hey Admin, you have successfully removed the user!"

    #
    # Define a static method - doesn't depend on self or class
    @staticmethod
    def review_user():
        return "Hey Admin, you have successfully reviewed the user"


#
# Instantiate User class
user_1 = User('jane', 'jane@gmail.com', '1234')
#
# Access the user attributes
jina = user_1.username
barua_pepe = user_1.email
#
# Access the user methods
login_status = user_1.login()
logout_status = user_1.logout()
# review = user_1.review_user()
#
# Instantiate Admin class
admin_1 = Admin('doe', 'doe@gmail.com', '5678')
#
# Access the user attributes
jina_admin = admin_1.username
barua_pepe_admin = admin_1.email
#
# Access the admin methods
login_status_admin = admin_1.login()
logout_status_admin = admin_1.logout()
review = admin_1.review_user()
add_user = admin_1.add_user()
print('f')
