class Bot(Client):

    
    def Answer_The_Question(self):
        bot_choice = random.choice(["Y", "N",])
        self.client_TCP.sendall(answer.encode())
