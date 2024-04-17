import errno
import socket
import time
import threading
import random
import copy
from tabulate import tabulate

# ------------------------------------------ Helper function ------------------------------------------------

"""
Chooses a random color for printing messages.

Returns:
    str: ANSI color code.
"""
def choose_Color():
    # GREEN, YELLOW, BLUE, CYAN, Light_Yellow, light_Blue, Light_Cyan
    color_array = ['\033[32m', '\033[33m', '\033[34m', '\033[36m', '\033[93m', '\033[94m', '\033[96m']

    return random.choice(color_array)


"""
Prints a message with a specified color.

Parameters:
    message (str): The message to be printed.
    color (str): The ANSI color code. Default is red.
"""
def print_with_color(message, color='\033[31m'):
    print(color + message + '\033[0m')


"""
Crafts an offer packet to be sent to clients.

Parameters:
    SERVER_PORT (int): The port on which the server is listening.

Returns:
    bytes: The offer packet to be sent.
"""
def craft_offer_packet(SERVER_PORT):
    # Magic cookie for identification
    magic_cookie = b'\xab\xcd\xdc\xba'
    # Type of message (0x02 for offer)
    message_type = b'\x02'
    # Server name padded to 32 bytes
    server_name = "TriviaKing".ljust(32, '\x00').encode('utf-8')
    # Server port in network byte order (big-endian)
    server_port = SERVER_PORT.to_bytes(2, byteorder='big')

    offer_packet = magic_cookie + message_type + server_name + server_port
    return offer_packet


# ------------------------------------------ Server class ------------------------------------------------

"""
This class represents a server for multiplayer gaming.
It manages the interaction between multiple clients, handling connections,
sending offer announcements, managing gameplay, and determining the winner.
The server provides a centralized platform for clients to connect,
exchange messages, and participate in multiplayer games.
"""
class Server:
    """
    Initializes a Server object with the following attributes:
    - BROADCAST_PORT: The port number used for broadcasting offer announcements.
    - SERVER_IP: The IP address of the server.
    - Server_UDP: Represents the UDP socket for sending offer announcements.
    - Server_TCP: Represents the TCP socket for accepting client connections.
    - StopOffer: A flag to control the offer announcement thread.
    - clients_information: A list to store information about connected clients.
      Each entry contains the client's name, socket, thread, score, and color.
    - client_answer: A list to store the answers of each client during gameplay.
    - winner: The name of the winning client.
    - Round: The current round of the game.
    - countBot: The count of bot clients connected to the server.
    - trivia_questions: A list of trivia questions for the game.
    - copy_questions: A copy of trivia_questions to ensure questions are not repeated.
    """
    def __init__(self):
        self.BROADCAST_PORT = 13117
        self.SERVER_IP, self.Server_UDP, self.Server_TCP = 0, 0, 0
        self.StopOffer = False
        self.clients_information, self.client_answer = [], []
        self.winner = ""
        self.Round = 1
        self.countBot = 0
        self.bestScoreEver = ["", 0]
        self.trivia_questions = [
            {"question": "Paris is the capital city of France.", "is_true": True},
            {"question": "Berlin is the capital city of Germany.", "is_true": True},
            {"question": "Rome is the capital city of Italy.", "is_true": True},
            {"question": "London is the capital city of England.", "is_true": False},
            {"question": "Madrid is the capital city of Spain.", "is_true": True},
            {"question": "Athens is the capital city of Greece.", "is_true": True},
            {"question": "Vienna is the capital city of Austria.", "is_true": True},
            {"question": "Stockholm is the capital city of Denmark.", "is_true": False},
            {"question": "Lisbon is the capital city of Portugal.", "is_true": True},
            {"question": "Dublin is the capital city of Ireland.", "is_true": True},
            {"question": "Warsaw is the capital city of Poland.", "is_true": True},
            {"question": "Brussels is the capital city of Switzerland.", "is_true": False},
            {"question": "Oslo is the capital city of Norway.", "is_true": True},
            {"question": "Moscow is the capital city of Russia.", "is_true": True},
            {"question": "Helsinki is the capital city of Finland.", "is_true": True},
            {"question": "Amsterdam is the capital city of the Netherlands.", "is_true": False},
            {"question": "Prague is the capital city of the Czech Republic.", "is_true": True},
            {"question": "Bern is the capital city of Switzerland.", "is_true": False},
            {"question": "Tallinn is the capital city of Lithuania.", "is_true": False},
            {"question": "Belgrade is the capital city of Croatia.", "is_true": False},
            {"question": "Bratislava is the capital city of Slovakia.", "is_true": True},
            {"question": "Vilnius is the capital city of Latvia.", "is_true": False},
            {"question": "Ljubljana is the capital city of Slovenia.", "is_true": False},
        ]

        self.copy_questions = copy.deepcopy(self.trivia_questions)


    """
    Gets the IP address of the server.
    """
    def get_ip_address(self):
        while True:
            # Create a socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # Connect to a remote server
                s.connect(("8.8.8.8", 80))
                # Get the local IP address of the socket
                self.SERVER_IP = s.getsockname()[0]
                # Break out of the loop if successful
                break

            except socket.error:
                pass

            finally:
                # Close the socket
                s.close()


    """
    Finds a free port for the server to listen on, and create UDP socket with this port.
    
    Returns:
        int: The port number found.
    """
    def findFreePort(self):
        # Get the IP address of the server
        self.get_ip_address()
        # Set the initial port number to 5000
        SERVER_PORT = 5000

        # Loop until a free port is found
        while True:
            try:
                # Create a UDP socket
                self.Server_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Attempt to bind the socket to the server IP address and the current port number
                self.Server_UDP.bind((self.SERVER_IP, SERVER_PORT))

            except OSError as e:
                # If the socket is already in use
                if e.errno == errno.EADDRINUSE:
                    # Increment the port number and try again
                    SERVER_PORT += 1
                    continue

            # Return the port number found
            return SERVER_PORT


    """
    Starts the server by setting up necessary sockets, broadcasting offer announcements,
    and listening for client connections.
    """
    def startServer(self):
        # Find a free port for the server to listen on
        SERVER_PORT = self.findFreePort()
        # Set socket options to allow broadcasting
        self.Server_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        print_with_color(f"Server started, listening on IP address {self.SERVER_IP}", '\033[92m')

        # Create a thread for sending offer announcements
        threading.Thread(target=self.send_offer_announcements, args=(SERVER_PORT,), daemon=True).start()

        # Continuously listen for client connections until at least one client connects
        while len(self.clients_information) == 0:
            # Listen for client names
            self.listen_for_clients(SERVER_PORT)

        self.start_game()


    """
    Listens for incoming client connections on the specified server port.

    Parameters:
        SERVER_PORT (int): The port on which the server is listening.
    """
    def listen_for_clients(self, SERVER_PORT):
        # Create a TCP socket for accepting client connections
        self.Server_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Bind the TCP server socket to the server IP address and port
            self.Server_TCP.bind((self.SERVER_IP, SERVER_PORT))
            # Enable the server to accept incoming connections
            self.Server_TCP.listen()

            # Continuously listen for incoming client connections
            while True:
                try:
                    # Set a timeout for accepting incoming connections
                    self.Server_TCP.settimeout(10)
                    # Accept an incoming client connection
                    client_socket, _ = self.Server_TCP.accept()
                    # Reset the timeout after accepting the connection
                    self.Server_TCP.settimeout(None)
                    # Create a thread to handle the new client
                    threading.Thread(target=self.save_user, args=(client_socket,), daemon=True).start()

                # Break out of the loop if no connections are received within the timeout period
                except socket.timeout:
                    break

                # Print any socket errors encountered during the process
                except socket.error as e:
                    print_with_color(f"Socket error: {e}")
                    continue

        # Print any OS errors encountered during the process
        except OSError as e:
            print_with_color(f"OS error occurred: {e}")


    """
    Receives the player name from the client and saves the client information.

    Args:
        client_socket (socket.socket): The socket object for the client connection.
    """
    def save_user(self, client_socket):
        # Receive the player name from the client
        try:
            player_name = client_socket.recv(1024).decode().strip()

            # If the player name is "BOT", generate a unique name
            if player_name == "BOT":
                self.countBot += 1
                player_name = f"BOT{self.countBot}"
                client_socket.sendall(player_name.encode('utf-8'))

            # Append client information to the list (name, socket, thread, score, color)
            self.clients_information.append([player_name, client_socket, 0, 0, choose_Color()])

        # Print any OS errors encountered during the process
        except OSError as e:
            print_with_color(f"Error with client socket: {e}")


    """
    Sends offer announcements to clients on the network.

    Args:
        SERVER_PORT (int): The port on which the server is listening.
    """
    def send_offer_announcements(self, SERVER_PORT):
        while not self.StopOffer:
            try:
                # Craft and send the offer announcement packet
                offer_packet = craft_offer_packet(SERVER_PORT)
                self.Server_UDP.sendto(offer_packet, ('<broadcast>', self.BROADCAST_PORT))
                print_with_color("Offer announcement sent", '\033[92m')

                # Sleep for 1 second before sending the next offer
                time.sleep(1)

            # Print any OS errors encountered during the process
            except OSError as e:
                print_with_color(f"An OS error occurred in the offer thread: {e}")

        self.Server_UDP.close()


    """
    Displays the list of current players to the server console and sends it to all active clients.
    """
    def Show_Players(self):
        Show_Players = ""
        # Loop through each active client
        for index, client_info in enumerate(self.clients_information):
            # Construct the string representation of the player
            curr = f"Player {index + 1}: {client_info[0]}\n"
            Show_Players += curr
            print_with_color(curr[:-1], client_info[4])

        print("")
        # Send the current players to all active clients
        for client_info in self.clients_information:
            try:
                # Send the current players to the client
                client_info[1].sendall(Show_Players.encode('utf-8'))
            # If there's an OSError, continue to the next client
            except OSError:
                continue

    """
    Sends a welcome message to newly connected clients and displays current players.

    Returns:
        bool: True if there are new clients, False otherwise.
    """
    def send_welcome_message(self):
        # List to store information about active clients.
        active_clients_information = []

        welcome_message = "\nWelcome to the TriviaKing server, where we are answering trivia questions about capitals cities in europe."
        # Check who is still active among all those registered for the game
        for client_info in self.clients_information:
            try:
                # Send the welcome message to the client
                client_info[1].sendall(welcome_message.encode('utf-8'))
            # If there's an OSError, continue to the next client
            except OSError:
                continue
            # If the message is sent successfully, add the client's information to the list of active clients
            active_clients_information.append(client_info)
            # Initialize the client's answer status
            self.client_answer.append(False)

        # If there are active clients, print the welcome message
        if len(active_clients_information) > 0:
            print(welcome_message)

        # Update the list of clients' information to only include the active clients
        self.clients_information = active_clients_information

        self.Show_Players()

        return len(self.clients_information) > 0


    """
    Handles the question-answer interaction with each connected client.

    Parameters:
        client_info (list): Information about the client, including the client socket.
        question (str): The question to be sent to the client.
        answer (bool): The correct answer to the question.
        index (int): The index of the client in the clients_information list.
    """
    def handler_question_per_client(self, client_info, question, answer, index):
        try:
            # Send the question to the client
            client_info[1].sendall(question.encode('utf-8'))
            # Record the start time for timeout calculation
            startTime = time.time()
            # Set a timeout of 10 seconds for receiving client response
            client_info[1].settimeout(10)
        # If an OSError occurs, close the client socket and mark it as None
        except OSError:
            client_info[1].close()
            client_info[1] = None
            self.client_answer[index] = False
            return

        try:
            # Loop until a valid answer is received or timeout occurs
            while True:
                # Receive the player's answer
                player_answer = client_info[1].recv(1024).decode()
                # Check if the received answer is valid
                if player_answer in ['Y', 'T', '1', 'N', 'F', '0']:
                    break
                # If the answer is invalid, send a message indicating invalid input
                else:
                    client_info[1].sendall("Invalid input".encode('utf-8'))
                # Adjust the timeout based on the time elapsed since the start
                client_info[1].settimeout(10 - (time.time() - startTime))

            # If the answer is correct, mark the client's answer as True and update correct answer count
            if (player_answer in ['Y', 'T', '1'] and answer) or (player_answer in ['N', 'F', '0'] and not answer):
                self.client_answer[index] = True
                client_info[3] += 1
            # If the answer is incorrect, mark the client's answer as False
            else:
                self.client_answer[index] = False

        # If a timeout occurs, mark the client's answer as False
        except socket.timeout:
            self.client_answer[index] = False

        # If a ConnectionResetError occurs, print a message and close the client socket
        except (ConnectionResetError, ConnectionAbortedError):
            print_with_color("Connection with the client crashed.")
            client_info[1].close()
            client_info[1] = None
            self.client_answer[index] = False

    """
    Calculates the clients who will participate in the next round.

    Returns:
        str: A formatted string indicating the clients participating in the next round.
    """
    def calculateNextRoundClients(self):
        # Prepare message for the next round
        nextRoundClient = f"\nRound {self.Round}, played by"
        for index, answer_client in enumerate(self.client_answer):
            # Check if the client continues to the next round
            if answer_client != None:
                nextRoundClient += f" {self.clients_information[index][0]} and"

        nextRoundClient = nextRoundClient[:-4] + ":"
        print(nextRoundClient)

        for index, answer_client in enumerate(self.client_answer):
            if answer_client != None:
                try:
                    self.clients_information[index][1].sendall(nextRoundClient.encode('utf-8'))
                except OSError:
                    continue


    """
    Chooses a random question from the available pool and prepares it for presentation to the players.

    Returns:
        tuple: A tuple containing the message for the next round 
        with the text of the chosen question and correct answer.
    """
    def choose_question(self):
        if len(self.copy_questions) == 0:
            return None, None

        # Choose random question
        random_question = random.choice(self.copy_questions)
        question_text = random_question["question"]
        correct_answer = random_question["is_true"]

        # Remove the chosen question from the list
        self.copy_questions.remove(random_question)

        # Check if it's not the first round
        if self.Round >= 2:
            self.calculateNextRoundClients()

        # Construct the question message
        question_message = f"True or false: {question_text}"

        # Print the next round information and the question message with color
        print_with_color(f"\033[1m{question_message}\033[0m", '\033[35m')

        # Return a tuple containing the question message and the answer text
        return question_message, correct_answer

    """
    Counts the number of correct answers given by players in the current round.

    Returns:
        int: The number of correct answers.
    """
    def checkHowManyCorrectAnswer(self):
        correctAns = 0
        for ans in self.client_answer:
            if ans == None:
                continue
            if ans:
                correctAns += 1
        return correctAns

    """
    Marks a client as having left the game.

    Parameters:
        indexOfClient (int): The index of the client in the clients_information list.
    """
    def markClientLeftTheGame(self, indexOfClient):
        # If the socket is open
        if self.clients_information[indexOfClient][1] is not None:
            # Close socket
            self.clients_information[indexOfClient][1].close()
            # Mark socket with None
            self.clients_information[indexOfClient][1] = None

        # Mark thread with None
        self.clients_information[indexOfClient][2] = None
        # Mark client_answer with None
        self.client_answer[indexOfClient] = None

    """
    Checks if the client is not active after giving an answer.

    Parameters:
        indexOfClient (int): The index of the client in the clients_information list.
        answer_client (bool): Whether the client's answer was correct or not.

    Returns:
        bool: True if the client is not active after giving an answer, False otherwise.
    """
    def checkIfClientNotActiveAfterGiveAnswer(self, indexOfClient, answer_client):
        # Check if the player left after giving an answer
        try:
            self.clients_information[indexOfClient][1].sendall("".encode('utf-8'))
            return False
        # If the player left
        except OSError:
            # If the client answered correctly before leaving the round
            if answer_client:
                # Subtract 1 from his score
                self.clients_information[indexOfClient][3] -= 1

            # Marks a client as having left the game.
            self.markClientLeftTheGame(indexOfClient)
            return True


    """
    Calculates the score for each player in the current round based on their answers.
    """
    def calculate_round_results(self):
        message = ""
        try:
            # Iterate through each client
            for index, answer_client in enumerate(self.client_answer):
                # If the player does not play this round
                if answer_client == None:
                    continue

                # If the player has left this round without entering an answer
                if self.clients_information[index][1] is None and not answer_client:
                    cur = f"{self.clients_information[index][0]} is left!\n"
                    # Mark the client as left
                    self.markClientLeftTheGame(index)

                # If the player left after giving an answer
                elif self.checkIfClientNotActiveAfterGiveAnswer(index, answer_client):
                    cur = f"{self.clients_information[index][0]} is left!\n"

                # If the client answered correctly
                elif answer_client:
                    cur = f"{self.clients_information[index][0]} is correct!\n"

                    # Check if this round will be declared the winner
                    if self.checkHowManyCorrectAnswer() == 1:
                        cur = cur[:-1] + f" {self.clients_information[index][0]} wins!\n"
                        self.winner = [self.clients_information[index][0], self.clients_information[index][4]]
                        if self.bestScoreEver[1] < self.clients_information[index][3]:
                            self.bestScoreEver = [self.clients_information[index][0], self.clients_information[index][3]]

                # If the customer answered incorrectly
                else:
                    cur = f"{self.clients_information[index][0]} is incorrect!\n"

                # Update the message
                message += cur
                print_with_color(cur[:-1], self.clients_information[index][4])

            # Increment the round counter
            self.Round += 1

            # Send the round result message to all clients
            for index, client_info in enumerate(self.clients_information):
                # Send to only client that play this round
                if client_info[2] is not None:
                    try:
                        client_info[1].sendall(message[:-1].encode('utf-8'))
                    except OSError:
                        # Mark the client as left
                        self.markClientLeftTheGame(index)

            # Check if everyone got it wrong, so they can play the next round
            if self.checkHowManyCorrectAnswer() == 0:
                return None

            # Eliminate the players who gave a wrong answer
            for index, answer_client in enumerate(self.client_answer):
                if not answer_client:
                    self.clients_information[index][2] = None
                    self.client_answer[index] = None

        except OSError as e:
            print_with_color(f"Error occurred in calculate_round_score: {e}")

    """
    Reset the game state and server settings.
    """
    def reset_game(self):
        for client_info in self.clients_information:
            if client_info[1] is not None:
                try:
                    client_info[1].close()
                except OSError:
                    continue

        if server.Server_UDP:
            server.Server_UDP.close()

        self.clients_information, self.client_answer = [], []
        self.copy_questions = copy.deepcopy(self.trivia_questions)
        self.Server_TCP.close()
        self.SERVER_IP, self.Server_TCP, self.countBot, self.Server_UDP, self.Round = 0, 0, 0, 0, 1
        self.StopOffer = False
        self.winner = ""

    """
    Prints a table displaying the scores of all clients.
    """
    def plot_table(self):
        print("\n")
        # Create bar graph
        score_table = [["Clients", "Score"]]
        for client in self.clients_information:
            score_table.append([client[0], client[3]])

        # Print table
        print(tabulate(score_table, headers="firstrow"))
        print("\n")
        print(f"Best score ever: {self.bestScoreEver[0]} with {self.bestScoreEver[1]} points")

    """
    Starts the game by sending welcome messages, choosing questions,
    handling answers, and determining the winner.
    """
    def start_game(self):
        # Set the flag to stop sending offer announcements
        self.StopOffer = True

        # If while sending a welcome message, you discover that there are no players
        if not self.send_welcome_message():
            self.reset_game()
            return

        # Continue the game until there's only one correct answer
        while self.checkHowManyCorrectAnswer() != 1:

            # Break the loop if all clients have disconnected
            if all(client_info[1] is None for client_info in self.clients_information):
                self.reset_game()
                print_with_color("\nGame over, sending out offer requests...\n", '\033[92m')
                return

            # Choose a question and answer for the round
            question, correct_answer = self.choose_question()
            if question == None:
                self.winner = "Draw"
                break

            # Start a thread for each active client to handle the question
            for index, client_info in enumerate(self.clients_information):
                if client_info[2] is not None:
                    client_info[2] = threading.Thread(target=self.handler_question_per_client,
                                                      args=(client_info, question, correct_answer, index),
                                                      daemon=True)
                    client_info[2].start()

            # Wait for all threads to finish their execution
            for client_info in self.clients_information:
                if client_info[2] is not None:
                    client_info[2].join()

            # Calculate the results of the round
            self.calculate_round_results()

        if self.winner == "Draw":
            message = f"\nGame over!\nThe game ended in a draw"
            print(message)

        else:
            message = f"\nGame over!\nCongratulations to the winner: {self.winner[0]}"
            print("\nGame over!\nCongratulations to the winner: " + self.winner[1] + f"{self.winner[0]}" + '\033[0m')

        for client_info in self.clients_information:
            if client_info[1] is not None:
                try:
                    client_info[1].sendall(message.encode('utf-8'))
                except OSError:
                    continue

        self.plot_table()
        self.reset_game()
        print_with_color("\nGame over, sending out offer requests...\n", '\033[92m')


if __name__ == "__main__":
    server = Server()
    while True:
        try:
            server.startServer()
        except KeyboardInterrupt:
            server.reset_game()
            break
