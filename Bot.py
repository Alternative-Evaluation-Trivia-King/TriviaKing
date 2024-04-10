import random
from Client import Client
from collections import Counter


class Bot(Client):

    def __init__(self):
        super().__init__()
        self.names = ["BOT"]
        self.trivia_questions_dic = {}
        self.yes_no_answers_counter = Counter({"Y": 0, "N": 0})
        self.messages_counter = 0
        self.bot_name = "" # bot name will given by the server
        self.last_answer = ""
        self.last_question = {}

    def Answer_The_Question(self):
        if self.last_question in self.trivia_questions_dic:
            bot_choice = self.trivia_questions_dic[self.last_question]
        else:
            bot_choice = self.yes_no_answers_counter.most_common(1)[0][0] # return the most common answer
        self.client_TCP.sendall(bot_choice.encode())
        self.last_answer = bot_choice

    def handle_message(self, message):
        if f"{self.bot_name} is correct" in message:    # if the bot was right in the last question
            self.trivia_questions_dic[self.last_question] = self.last_answer    # save bot's answer to the question
            self.yes_no_answers_counter[self.last_answer] += 1

        elif f"{self.bot_name} is incorrect" in message:    # if the bot was wrong in the last question

            ########################### save bot's oposite answer to the question ##################
            if self.last_answer == "Y":
                answer = "N"

            else:
                answer = "Y"
            #########################################################################################

            self.trivia_questions_dic[self.last_question] = answer
            self.yes_no_answers_counter[answer] += 1

        self.last_question = message.split("True or false: ")[1]

    def clientPlay(self):
        try:
            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')
                print(message)
                self.messages_counter += 1

                if "Welcome" in message:
                    continue

                elif "Game over!" in message:
                    self.client_TCP.close()
                    break

                # elif self.messages_counter == 2:  # The second massage that the server will send to the bot is the bot name
                #     self.bot_name = message

                else:
                    self.handle_message(message)


                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question, daemon=True)
                Answer_Question_Thread.start()

            print("Server disconnected, listening for offer requests...")

        except ConnectionResetError:
            print("Connection with server reset by peer.")
            self.client_TCP.close()


if __name__ == "__main__":
    bot = Bot()
    while True:
        bot.startClient()