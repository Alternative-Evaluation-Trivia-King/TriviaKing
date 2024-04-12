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
    # GREEN, YELLOW, BLUE, CYAN
    color_array = ['\033[32m', '\033[33m', '\033[34m', '\033[36m']

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

        print("Server started, listening on IP address", self.SERVER_IP)

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
                player_name = f"Bot{self.countBot}"
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
                print("Offer announcement sent")

                # Sleep for 1 second before sending the next offer
                time.sleep(1)

            # Print any OS errors encountered during the process
            except OSError as e:
                print_with_color(f"An OS error occurred in the offer thread: {e}")

        # self.Server_UDP.close()

    def Show_Players(self):
        Show_Players = ""
        # Loop through each active client
        for index, client_info in enumerate(self.clients_information):
            curr = f"Player {index + 1}: {client_info[0]}\n"
            Show_Players += curr
            print_with_color(curr[:-1], client_info[4])

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

        return len(self.clients_information ) > 0

    def handler_question_per_client(self, client_info, question, answer, index):
        startTime = 0
        try:
            client_info[1].sendall(question.encode('utf-8'))
            startTime = time.time()
            client_info[1].settimeout(10)  # Set a timeout of 10 seconds
        except OSError:
            client_info[1].close()
            client_info[1] = None
            self.client_answer[index] = False
            return

        try:
            while True:
                player_answer = client_info[1].recv(1024).decode()
                if player_answer in ['Y', 'T', '1', 'N', 'F', '0']:
                    break
                else:
                    client_info[1].sendall("Invalid input".encode('utf-8'))
                client_info[1].settimeout(10 - (time.time() - startTime))

            # Check if the player's answer is correct
            if (player_answer in ['Y', 'T', '1'] and answer) or (player_answer in ['N', 'F', '0'] and not answer):
                self.client_answer[index] = True
                client_info[3] += 1
            else:
                self.client_answer[index] = False

        except socket.timeout:
            self.client_answer[index] = False

        except ConnectionResetError:
            print_with_color("Connection with Client reset by peer.")
            client_info[1].close()
            client_info[1] = None
            self.client_answer[index] = False

    def choose_question(self):
        question_message = "\n"
        nextRoundClient = ""
        # Choose random question
        random_question = random.choice(self.copy_questions)
        question_text = random_question["question"]
        answer_text = random_question["is_true"]

        # Delete the chosen question from the list
        self.copy_questions.remove(random_question)

        if self.Round >= 2:
            nextRoundClient = f"\nRound {self.Round}, played by"
            for index, answer_client in enumerate(self.client_answer):
                if answer_client != -1 and not answer_client:
                    nextRoundClient += f" {self.clients_information[index][0]} and"
            nextRoundClient = nextRoundClient[:-3] + ":"

        question_message += f"True or false: {question_text}"

        print(nextRoundClient)
        print_with_color(f"\033[1m{question_message[1:]}\033[0m", '\033[35m')

        return (nextRoundClient + question_message), answer_text

    def checkStatusGame(self):
        wrongAns, correctAns = 0, 0
        for ans in self.client_answer:
            if ans == -1:
                continue
            if ans:
                correctAns += 1
        return correctAns

    def calculate_round_score(self):
        message = ""
        try:
            for index, answer_client in enumerate(self.client_answer):
                if answer_client == -1:
                    continue

                if self.clients_information[index][1] is None and not answer_client:
                    cur = f"{self.clients_information[index][0]} is left!\n"
                    message += cur
                    print_with_color(cur[:-1], self.clients_information[index][4])
                    continue

                try:
                    self.clients_information[index][1].sendall("".encode('utf-8'))
                except OSError:
                    self.clients_information[index][1] = None
                    self.clients_information[index][2] = None
                    if answer_client:
                        self.clients_information[index][3] -= 1
                    self.client_answer[index] = -1
                    cur = f"{self.clients_information[index][0]} is left!\n"
                    message += cur
                    print_with_color(cur[:-1], self.clients_information[index][4])
                    continue

                if answer_client:
                    cur = f"{self.clients_information[index][0]} is correct!\n"
                    message += cur

                    if self.checkStatusGame() == 1:
                        cur2 = f"{self.clients_information[index][0]} wins!\n"
                        message = message[:-1] + " " + cur2
                        self.winner = self.clients_information[index][0]

                        cur = cur[:-1] + " " + cur2

                    print_with_color(cur[:-1], self.clients_information[index][4])
                else:
                    cur = f"{self.clients_information[index][0]} is incorrect!\n"
                    message += f"{self.clients_information[index][0]} is incorrect!\n"
                    print_with_color(cur[:-1], self.clients_information[index][4])

            self.Round += 1

            for index, client_info in enumerate(self.clients_information):
                if client_info[1] is None:
                    client_info[2] = None
                    self.client_answer[index] = -1
                    continue

                if client_info[2] is not None:
                    try:
                        client_info[1].sendall(message.encode('utf-8'))
                    except OSError:
                        client_info[1] = None
                        client_info[2] = None
                        self.client_answer[index] = -1

            if self.checkStatusGame() == 0:
                return None

            for index, answer_client in enumerate(self.client_answer):
                if not answer_client:
                    self.clients_information[index][2] = None
                    self.client_answer[index] = -1

        except OSError as e:
            print_with_color(f"Error occurred in calculate_round_score: {e}")
            # Handle the error as needed, e.g., log it, close the connection, etc.

    def reset_game(self):
        self.clients_information, self.client_answer = [], []
        self.Round = 1
        self.copy_questions = copy.deepcopy(self.trivia_questions)
        self.Server_TCP.close()
        self.SERVER_IP, self.Server_TCP = 0, 0
        self.StopOffer = False

    def plot_table(self):
        print("\n")
        # Create bar graph
        score_table = [["Clients", "Score"]]
        for client in self.clients_information:
            score_table.append([client[0], client[3]])

        print(tabulate(score_table, headers="firstrow"))

    def start_game(self):
        try:
            self.StopOffer = True

            if not self.send_welcome_message():
                self.reset_game()
                return

            while self.checkStatusGame() != 1:
                if all(socket[1] is None for socket in self.clients_information):
                    break
                question, answer = self.choose_question()
                for index, client_info in enumerate(self.clients_information):
                    if client_info[2] is not None:
                        client_info[2] = threading.Thread(target=self.handler_question_per_client,
                                                          args=(client_info, question, answer, index),
                                                          daemon=True)
                        client_info[2].start()

                # Wait for all threads to finish their execution
                for client_info in self.clients_information:
                    if client_info[2] is not None:
                        client_info[2].join()

                self.calculate_round_score()

            message = f"\nGame over!\nCongratulations to the winner: {self.winner}"
            for client_info in self.clients_information:
                if client_info[1] is not None:
                    client_info[1].sendall(message.encode('utf-8'))
                    client_info[1].close()

            self.plot_table()
            print("\nGame over, sending out offer requests...\n")

            self.reset_game()

        except OSError as e:
            print_with_color("Error occurred in start_game: {e}")
            # Handle the error as needed, e.g., log it, close the connection, etc.


if __name__ == "__main__":
    server = Server()
    while True:
        server.startServer()
