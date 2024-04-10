import errno
import socket
import time
import threading
import random
import copy
import matplotlib.pyplot as plt

'''----------------------------------------- Global variable --------------------------------------------------'''

BROADCAST_PORT = 13117
SERVER_IP, Server_UDP, Server_TCP = 0, 0, 0
StopOffer = False
clients_information, client_answer = [], []
winner = ""
Round = 1
countBot = 0

trivia_questions = [
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

copy_questions = copy.deepcopy(trivia_questions)

'''------------------------------------------------------------------------------------------------------'''


def get_ip_address():
    global SERVER_IP
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a remote server (doesn't matter which one)
        s.connect(("8.8.8.8", 80))
        # Get the local IP address of the socket
        SERVER_IP = s.getsockname()[0]
    finally:
        # Close the socket
        s.close()


def findFreePort():
    global Server_UDP
    get_ip_address()
    SERVER_PORT = 5000
    while True:
        try:
            # Try open socket
            Server_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Try bind with this socket
            Server_UDP.bind((SERVER_IP, SERVER_PORT))

        except OSError as e:
            # If socket is in use
            if e.errno == errno.EADDRINUSE:
                # Try another Socket
                SERVER_PORT += 1
                continue

        # Return desired socket
        return SERVER_PORT


def server():
    global Server_UDP
    # Create a UDP socket
    SERVER_PORT = findFreePort()
    # Set socket options to allow broadcasting
    Server_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print("Server started, listening on IP address", SERVER_IP)

    # Create a thread for sending offer announcements
    threading.Thread(target=send_offer_announcements, args=(Server_UDP, SERVER_PORT), daemon=True).start()

    # Listen for client names
    while len(clients_information) == 0:
        listen_for_clients(SERVER_PORT)
    start_game()


def listen_for_clients(SERVER_PORT):
    global Server_TCP
    # Create a TCP socket for accepting client connections
    Server_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the tcp server socket to IP and Port
        Server_TCP.bind((SERVER_IP, SERVER_PORT))
        # Enable to accept incoming connections
        Server_TCP.listen()

        while True:
            try:
                Server_TCP.settimeout(10)
                # Accept incoming client connection
                client_socket, _ = Server_TCP.accept()
                Server_TCP.settimeout(None)
                # Create a thread for save user
                threading.Thread(target=save_user, args=(client_socket,), daemon=True).start()

            except socket.timeout:
                break

            except KeyboardInterrupt:
                print("Listening thread shutting down...")
                break

            except socket.error as e:
                print(f"Socket error: {e}")
                continue
    except OSError as e:
        print(f"OS error occurred: {e}")


def save_user(client_socket):
    global countBot
    # Receive player name from client
    try:
        player_name = client_socket.recv(1024).decode().strip()

        if player_name == "BOT":
            countBot += 1
            player_name = f"Bot{countBot}"
            client_socket.sendall(player_name.encode('utf-8'))

        clients_information.append([player_name, client_socket, 0, 0])

    except OSError as e:
        print(f"Error with client socket: {e}")


def send_offer_announcements(server_socket, SERVER_PORT):
    while not StopOffer:
        try:
            # Craft and send the offer announcement packet
            offer_packet = craft_offer_packet(SERVER_PORT)
            server_socket.sendto(offer_packet, ('<broadcast>', BROADCAST_PORT))
            print("Offer announcement sent")

            # Sleep for 1 second before sending the next offer
            time.sleep(1)

        except KeyboardInterrupt:
            print("Offer thread shutting down...")
            break

        except OSError as e:
            print(f"An OS error occurred in the offer thread: {e}")
            # Handle the OS error as needed, e.g., log it, attempt recovery, etc.

    # server_socket.close()


# Craft the offer announcement packet
def craft_offer_packet(SERVER_PORT):
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name = "MyServer".ljust(32, '\x00').encode('utf-8')
    server_port = SERVER_PORT.to_bytes(2, byteorder='big')

    offer_packet = magic_cookie + message_type + server_name + server_port
    return offer_packet


def send_welcome_message():
    global clients_information
    new_clients_information = []
    welcome_message = "\nWelcome to MyServer server, where we are answering trivia questions about capitals cities in europe."
    for client_info in clients_information:
        try:
            client_info[1].sendall(welcome_message.encode('utf-8'))
        except OSError:
            continue

        new_clients_information.append(client_info)
        client_answer.append(False)

    clients_information = new_clients_information
    Show_Players = ""
    for index, client_info in enumerate(clients_information):
        Show_Players += f"Player {index + 1}: {client_info[0]}\n"

    for client_info in clients_information:
        try:
            client_info[1].sendall(Show_Players.encode('utf-8'))
        except OSError:
            continue

    if (len(new_clients_information)) > 0:
        print(welcome_message)
        print(Show_Players)
        return True
    else:
        return False


def handler_question_per_client(client_info, question, answer, index):
    try:
        client_info[1].sendall(question.encode('utf-8'))
        client_info[1].settimeout(10)  # Set a timeout of 10 seconds
    except OSError:
        client_info[1].close()
        client_info[1] = None
        client_answer[index] = False
        return

    try:
        player_answer = client_info[1].recv(1024).decode()
        # Check if the player's answer is correct
        if (player_answer in ['Y', 'T', '1'] and answer) or (player_answer in ['N', 'F', '0'] and not answer):
            client_answer[index] = True
            client_info[3] += 1
        else:
            client_answer[index] = False

    except socket.timeout:
        client_answer[index] = False

    except ConnectionResetError:
        print("Connection with Client reset by peer.")
        client_info[1].close()
        client_info[1] = None
        client_answer[index] = False


def choose_question():
    global copy_questions
    question_message = ""
    # Choose random question
    random_question = random.choice(copy_questions)
    question_text = random_question["question"]
    answer_text = random_question["is_true"]

    print(question_text)
    # Delete the chosen question from the list
    copy_questions.remove(random_question)

    if Round >= 2:
        question_message = f"Round {Round}, played by"
        for index, answer_client in enumerate(client_answer):
            if answer_client != -1 and not answer_client:
                question_message += f" {clients_information[index][0]} and"
        question_message = question_message[:-3] + "\n"

    question_message += f"True or false: {question_text}\n"
    return question_message, answer_text


def checkStatusGame():
    wrongAns, correctAns = 0, 0
    for ans in client_answer:
        if ans == -1:
            continue
        if ans:
            correctAns += 1
    return correctAns


def calculate_round_score():
    global winner, Round
    message = ""
    try:
        for index, answer_client in enumerate(client_answer):
            if answer_client == -1:
                continue

            elif clients_information[index][1] is None and not answer_client:
                message += f"\n{clients_information[index][0]} is left!"

            elif answer_client:
                message += f"\n{clients_information[index][0]} is correct!"
                if checkStatusGame() == 1:
                    message += f" {clients_information[index][0]} wins!\n"
                    winner = clients_information[index][0]
            else:
                message += f"\n{clients_information[index][0]} is incorrect!"
        Round += 1
        print(message)

        for index, client_info in enumerate(clients_information):
            if client_info[1] is None:
                client_info[2] = None
                client_answer[index] = -1
                continue

            if client_info[2] is not None:
                try:
                    client_info[1].sendall(message.encode('utf-8'))
                except OSError:
                    client_info[1] = None
                    client_info[2] = None
                    client_answer[index] = -1

        if checkStatusGame() == 0:
            return None

        for index, answer_client in enumerate(client_answer):
            if not answer_client:
                clients_information[index][2] = None
                client_answer[index] = -1

    except OSError as e:
        print(f"Error occurred in calculate_round_score: {e}")
        # Handle the error as needed, e.g., log it, close the connection, etc.


def reset_game():
    global Server_TCP, StopOffer, Round, clients_information, copy_questions, SERVER_IP, Server_UDP, client_answer
    clients_information, client_answer = [], []
    Round = 1
    copy_questions = copy.deepcopy(trivia_questions)
    Server_TCP.close()
    SERVER_IP, Server_TCP = 0, 0
    StopOffer = False


def plot_graph():
    # Create bar graph
    names = [client[0] for client in clients_information]
    plt.bar(names)

    # Add labels and title
    plt.xlabel('Client')
    plt.ylabel('Score')
    plt.title('Bar Graph Example')

    # Show plot
    plt.show()


def start_game():
    global StopOffer, clients_information, Round, winner

    try:
        StopOffer = True

        if not send_welcome_message():
            reset_game()
            return

        while checkStatusGame() != 1:
            if all(socket[1] is None for socket in clients_information):
                break
            question, answer = choose_question()
            for index, client_info in enumerate(clients_information):
                if client_info[2] is not None:
                    client_info[2] = threading.Thread(target=handler_question_per_client,
                                                      args=(client_info, question, answer, index),
                                                      daemon=True)
                    client_info[2].start()

            # Wait for all threads to finish their execution
            for client_info in clients_information:
                if client_info[2] is not None:
                    client_info[2].join()

            calculate_round_score()

        message = f"Game over!\nCongratulations to the winner: {winner}"
        for client_info in clients_information:
            if client_info[1] is not None:
                client_info[1].sendall(message.encode('utf-8'))
                client_info[1].close()

        # plot_graph()
        print("Game over, sending out offer requests...")

        reset_game()

    except OSError as e:
        print(f"Error occurred in start_game: {e}")
        # Handle the error as needed, e.g., log it, close the connection, etc.


if __name__ == "__main__":
    while True:
        server()
