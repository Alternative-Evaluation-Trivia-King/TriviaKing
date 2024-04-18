import random
import re
import time
from Client import Client
from Server import print_with_color

"""
A class representing a bot client for a trivia game.
"""
class Bot(Client):

    """
    Initializes a Bot instance with attributes:
    names (list): A list of possible names for the bot.
    trivia_questions_dic (dict): A dictionary to store the trivia questions and their corresponding answers.
    bot_name (str): The name of the bot assigned by the server.
    last_answer (str): The last answer given by the bot.
    last_question (str): The last question received by the bot.
    """
    def __init__(self):
        # Call the constructor of the parent class
        super().__init__()
        self.names = ["BOT"]
        self.trivia_questions_dic = {}
        self.bot_name = ""
        self.last_answer = ""
        self.last_question = ""


    """
    Checks the bot answer if correct.

    Args:
        message (str): The message received from the server.
    """
    def check_bot_answer(self, message):
        # Check if the bot was wrong in the last question
        if f"{self.bot_name} is incorrect" in message:
            # If the bot was wrong, toggle the answer for the last question
            self.last_answer = "N" if self.last_answer == "Y" else "Y"

        # Save the correct answer for the last question
        self.trivia_questions_dic[self.last_question] = self.last_answer


    """
    Answers the True or False question received from the server.

    Args:
        message (str): The question message received from the server.
    """
    def Guess_Or_Search_The_Answer(self, message):
        time.sleep(1)
        # Extract the question from the message
        self.last_question = message
        # Get the last answer for this question from the dictionary, or choose a random answer if not found
        self.last_answer = self.trivia_questions_dic.get(self.last_question, random.choice(["Y", "N"]))
        # Send the answer back to the server
        self.client_TCP.sendall(self.last_answer.encode())
        print(self.last_answer)


    """
    Handles the gameplay logic for the bot client.
    This method receives messages from the server, processes them, and responds accordingly.
    """
    def clientPlay(self):
        try:
            while True:
                # Receive message from the server
                message = self.client_TCP.recv(1024).decode('utf-8')

                # If the message is the bot's name, set the bot name attribute
                if re.match(r'^BOT\d+$', message):
                    self.bot_name = message
                    continue

                # Check if the game is over
                if "Game over!" in message:
                    print_with_color(message, '\033[33m')
                    self.client_TCP.close()
                    break

                # If the message contains a question, answer it
                elif "True or false" in message:
                    print_with_color(f"\033[1m{message}\033[0m", '\033[35m')
                    self.Guess_Or_Search_The_Answer(message)

                # If the message contains information about correct or incorrect answers, handle it
                elif "correct" in message or "incorrect" in message:
                    print_with_color(message, '\033[33m')
                    self.check_bot_answer(message)

                else:
                    print_with_color(message, '\033[33m')

            print_with_color("\nServer disconnected, listening for offer requests...\n", '\033[92m')

        except (ConnectionResetError, ConnectionAbortedError):
            print_with_color("Connection with the server crashed.")
            self.client_TCP.close()


if __name__ == "__main__":
    bot = Bot()
    while True:
        try:
            bot.startClient()
            bot.clientPlay()

        except KeyboardInterrupt:
            if bot.client_UDP:
                bot.client_UDP.close()
            if bot.client_TCP:
                bot.client_TCP.close()
            break
