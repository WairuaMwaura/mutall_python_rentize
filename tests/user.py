# File Objective: Create a test class to demonstrate how classes are implemented
#   in Python
class User:
    def __init__(self, username, email, password):
        #
        # Initialize the attributes (variables for a class)
        self.username = username
        self.email = email

        self.password = password

    #
    # Initialize methods (functions for a class)
    def login(self):
        return f"{self.username.title()} successfully logged in!"

    def logout(self):
        return f"{self.username.title()} successfully logged out!"

    def update_username(self, new_username):
        self.username = new_username
        return (f"You have successfully changed your username to "
                f"{self.username.title()}")
