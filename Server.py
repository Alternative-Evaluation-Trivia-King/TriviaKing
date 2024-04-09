import errno
import socket
import time
import threading
import random

'''----------------------------------------- Global variable --------------------------------------------------'''

BROADCAST_PORT = 13117
SERVER_IP, timer_thread, server_socket = None, None, None
clients_information = []
StopOffer, StopListen = False, False

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
    {"question": "Copenhagen is the capital city of Sweden.", "is_true": True},
    {"question": "Budapest is the capital city of Hungary.", "is_true": True},
    {"question": "Helsinki is the capital city of Finland.", "is_true": True},
    {"question": "Amsterdam is the capital city of the Netherlands.", "is_true": False},
    {"question": "Prague is the capital city of the Czech Republic.", "is_true": True},
    {"question": "Bern is the capital city of Switzerland.", "is_true": False},
    {"question": "Sofia is the capital city of Bulgaria.", "is_true": True},
    {"question": "Tallinn is the capital city of Lithuania.", "is_true": False},
    {"question": "Belgrade is the capital city of Croatia.", "is_true": False},
    {"question": "Bucharest is the capital city of Romania.", "is_true": True},
    {"question": "Bratislava is the capital city of Slovakia.", "is_true": True},
    {"question": "Vilnius is the capital city of Latvia.", "is_true": False},
    {"question": "Ljubljana is the capital city of Slovenia.", "is_true": False},
    {"question": "Tirana is the capital city of Albania.", "is_true": True},
    {"question": "Skopje is the capital city of Macedonia.", "is_true": True},
    {"question": "Podgorica is the capital city of Montenegro.", "is_true": True},
]


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


def server():
    global server_socket
    # Create a UDP socket
    SERVER_PORT, server_socket = findFreePort()
    # Set socket options to allow broadcasting
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print("Server started, listening on IP address", SERVER_IP)

    # Create a thread for sending offer announcements
    threading.Thread(target=send_offer_announcements, args=(server_socket, SERVER_PORT), daemon=True).start()

    # Listen for client names
    listen_for_clients(SERVER_PORT)


def listen_for_clients(SERVER_PORT):
    # Create a TCP socket for accepting client connections
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind the tcp server socket to IP and Port
    tcp_server_socket.bind((SERVER_IP, SERVER_PORT))
    # Enable to accept incoming connections
    tcp_server_socket.listen()

    while not StopListen:
        try:
            # Accept incoming client connection
            client_socket, _ = tcp_server_socket.accept()
            # Create a thread for save user
            threading.Thread(target=save_user, args=(client_socket,), daemon=True).start()

        except KeyboardInterrupt:
            print("Listening thread shutting down...")
            break

        except socket.error as e:
            continue


def save_user(client_socket):
    global timer_thread
    # Receive player name from client
    player_name = client_socket.recv(1024).decode().strip()
    clients_information.append((player_name, client_socket))

    # Start or reset the timer
    if timer_thread is not None:
        timer_thread.cancel()
    timer_thread = threading.Timer(10, start_game)
    timer_thread.start()


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


def findFreePort():
    global server_socket
    get_ip_address()
    SERVER_PORT = 5000
    while True:
        try:
            # Try open socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Try bind with this socket
            server_socket.bind((SERVER_IP, SERVER_PORT))

        except OSError as e:
            # If socket is in use
            if e.errno == errno.EADDRINUSE:
                # Try another Socket
                SERVER_PORT += 1
                continue

        # Return desired socket
        return SERVER_PORT, server_socket


# Craft the offer announcement packet
def craft_offer_packet(SERVER_PORT):
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name = "MyServer".ljust(32, '\x00').encode('utf-8')
    server_port = SERVER_PORT.to_bytes(2, byteorder='big')

    offer_packet = magic_cookie + message_type + server_name + server_port
    return offer_packet


def send_welcome_message():
    welcome_message = ""
    for client_info in clients_information:
        welcome_message = f"Welcome, {client_info[0]}! Welcome to MyServer server, where we are answering trivia questions about capitals cities in europe.\n"
        for index, client in enumerate(clients_information):
            welcome_message += f"Player {index}: {client[0]}\n\n\n"

    print(welcome_message.split("! ")[1])


def start_game():
    global StopOffer, StopListen
    StopOffer, StopListen = True, True

    send_welcome_message()

    while True:
        # Choose random question
        random_question = random.choice(trivia_questions)
        question_text = random_question["question"]
        question_message = f"True or false: {question_text}\n"
        # Delete the chosen question from the list
        trivia_questions.remove(random_question)

        # client_info[1].sendall(question_message.encode())

    # StopOffer = False
    # StopListen = False


if __name__ == "__main__":
    server()
