import time

from Client import Client
from collections import Counter
import threading


class Bot(Client):

    def __init__(self):
        super().__init__()
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

        self.last_question = message.split("True or false: ", 1)[-1]

    def Answer_The_Question2(self, message):

        self.handle_message(message)
        mostChoice = self.yes_no_answers_counter.most_common(1)[0][0]
        self.last_answer = self.trivia_questions_dic.get(self.last_question, mostChoice)
        self.client_TCP.sendall(self.last_answer.encode())




    def clientPlay(self):
        try:
            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')
                if not message.startswith("BOT"):
                    print(message)

                if "Welcome" in message:
                    continue

                elif message.startswith("BOT"):
                    self.bot_name = message
                    continue

                # else:
                #     self.handle_message(message)

                elif "Game over!" in message:
                    self.client_TCP.close()
                    break



                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question2,
                                                          args=(message,),
                                                          daemon=True)
                Answer_Question_Thread.start()

                time.sleep(1)

            print("Server disconnected, listening for offer requests...")

        except ConnectionResetError as e:
            print(e)
            self.client_TCP.close()


if __name__ == "__main__":
    bot = Bot()
    while True:
        bot.startClient()
        bot.clientPlay()
