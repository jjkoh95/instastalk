import UserDALC
import time

class User():
    def __init__(self):
        self.email = None
        self.cookie = None
        self.last_login = None
    
    def login(self, email, cookie):
        self.email = email
        self.cookie = cookie
        self.last_login = time.time()
        UserDALC.insert(self.email, self.cookie, self.last_login)

    def logout(self):
        UserDALC.delete(self.email) 

    def loginOldEmail(self, email):
        row_data = UserDALC.getUser(email)
        self.email = row_data[0]
        self.cookie = row_data[1]
        self.last_login = row_data[2]
