import random
from Client import Client


class Bot(Client):

    def __init__(self):
        super().__init__()
        self.names = ["BOT"]
        self.trivia_questions_dic = {}
        self.yes_no_answers_dic = {}
        self.messages_counter = 0
        self.bot_name = "" # bot name will given by the server
        self.last_answer = ""
        self.last_question = {}

    def Answer_The_Question(self):
        if self.last_question in self.trivia_questions_dic:
            bot_choice = self.trivia_questions_dic[self.last_question]
        else:
            bot_choice = random.choice(["Y", "N", ])
        self.client_TCP.sendall(bot_choice.encode())
        self.last_answer = bot_choice

    def clientPlay(self):
        try:
            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')
                print(message)
                self.messages_counter += 1

                if "Welcome" in message:
                    continue

                if "Game over!" in message:
                    self.client_TCP.close()
                    break

                if self.messages_counter == 2:  # The second massage that the server will send to the bot is the bot name
                    self.bot_name = message

                else:
                    if f"{self.bot_name} is correct" in message:
                        self.trivia_questions_dic[self.last_question] = self.last_answer
                    elif f"{self.bot_name} is incorrect" in message:
                        if self.last_answer == "Y":
                            self.trivia_questions_dic[self.last_question] = "N"
                        else:
                            self.trivia_questions_dic[self.last_question] = "Y"

                    self.last_question = message.split("True or false: ")[1]


                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question, daemon=True)
                Answer_Question_Thread.start()

            print("Server disconnected, listening for offer requests...")

        except ConnectionResetError:
            print("Connection with server reset by peer.")
            self.client_TCP.close()
