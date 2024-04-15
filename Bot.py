import re
import time

from Client import Client
from collections import Counter


class Bot(Client):

    def __init__(self):
        super().__init__()
        self.names = ["BOT"]
        self.trivia_questions_dic = {}
        self.yes_no_answers_counter = Counter({"Y": 0, "N": 0})
        self.bot_name = ""  # bot name will give by the server
        self.last_answer = ""
        self.last_question = ""


    def handle_message(self, message):
        if f"{self.bot_name} is correct" in message:  # if the bot was right in the last question
            self.trivia_questions_dic[self.last_question] = self.last_answer  # save bot's answer to the question
            self.yes_no_answers_counter[self.last_answer] += 1

        elif f"{self.bot_name} is incorrect" in message:  # if the bot was wrong in the last question
            # save bot's oposite answer to the question
            answer = "N" if self.last_answer == "Y" else "Y"

            self.trivia_questions_dic[self.last_question] = answer
            self.yes_no_answers_counter[answer] += 1


    def Answer_The_Question2(self, message):
        time.sleep(1)
        self.last_question = message.split("True or false: ", 1)[-1]
        mostChoice = self.yes_no_answers_counter.most_common(1)[0][0]
        self.last_answer = self.trivia_questions_dic.get(self.last_question, mostChoice)
        self.client_TCP.sendall(self.last_answer.encode())

    def clientPlay(self):
        try:
            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')

                if re.match(r'^BOT\d+$', message):
                    self.bot_name = message
                    continue

                print(message)

                if "Game over!" in message:
                    print(self.trivia_questions_dic)
                    self.client_TCP.close()
                    break

                if "True or false" in message:
                    self.Answer_The_Question2(message)

                elif "correct" in message or "incorrect" in message:
                    self.handle_message(message)

            print("Server disconnected, listening for offer requests...")

        except ConnectionResetError as e:
            print(e)
            self.client_TCP.close()


if __name__ == "__main__":
    bot = Bot()
    while True:
        bot.startClient()
        bot.clientPlay()
