class Bot(Client):


    def __init__(self):
        super().__init__()
        self.names = ["BOT1", "BOT2", "BOT2", "BOT4", "BOT5"]
    def Answer_The_Question(self):
        bot_choice = random.choice(["Y", "N",])
        self.client_TCP.sendall(answer.encode())
