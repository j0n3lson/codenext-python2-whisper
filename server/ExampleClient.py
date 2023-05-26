import requests
import json

class Game_Commands():

    def _init_(self, address: str, username: str):
        self.address = "http://127.0.0.1:5000"
        self.username = "User01"
        self.api_key = "0000"

    def set_address(self, new_address: str):
        self.address = new_address

    def Register(self, new_username: str, new_api_key: str):
        self.username = new_username
        self.api_key = new_api_key
        return "No register function yet."
    
    def Listen(self):
        http_address = self.address + "/play/listen/" + self.username
        output = requests.get(http_address)
        return output
    
    def Whisper(self, to_user: str, message: str):
        http_address = self.address + "/play/whisper/" + to_user
        '''
        json_tosend = {
            'api_key': self.api_key,
            'from_username': self.username,
            'message': message
        }
        Unsure here how to include this.
        '''
        requests.post(http_address, to_user)
    
# Changing ip address
# Game_Commands.set_address("")

# Registering user
# Game_Commands.Register("", "")

# Listening for Whispers
# print(Game_Commands.Listen())

# Whispering
# Game_Commands.Whisper("User02", "Hello User 2!")