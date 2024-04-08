import errno
import socket
import time
import threading

# Server configuration
BROADCAST_PORT = 13117
SERVER_IP = None  # Change this to the desired server IP address
clients_information = []
timer_thread = None
StopOffer = False
StopListen = False
server_socket = None

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
    offer_thread = threading.Thread(target=send_offer_announcements, args=(server_socket, SERVER_PORT))
    offer_thread.daemon = True  # Daemonize the thread so it terminates with the main thread
    offer_thread.start()

    # Listen for client names
    listen_for_clients(SERVER_PORT)


def listen_for_clients(SERVER_PORT):
    # Create a TCP socket for accepting client connections
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind((SERVER_IP, SERVER_PORT))
    tcp_server_socket.listen()

    while not StopListen:
        try:
            # Accept incoming client connection
            client_socket, client_address = tcp_server_socket.accept()
            save_user_thread = threading.Thread(target=save_user, args=(client_socket, client_address))
            save_user_thread.daemon = True  # Daemonize the thread so it terminates with the main thread
            save_user_thread.start()

        except KeyboardInterrupt:
            print("Listening thread shutting down...")
            break

        except socket.error as e:
            continue


def save_user(client_socket, client_address):
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
    get_ip_address()
    global server_socket
    SERVER_PORT = 5000
    while True:
        try:
            print(SERVER_IP)
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind((SERVER_IP, SERVER_PORT))

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                SERVER_PORT += 1
                continue

        return SERVER_PORT, server_socket



def craft_offer_packet(SERVER_PORT):
    # Craft the offer announcement packet
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name = "MyServer".ljust(32, '\x00').encode('utf-8')
    server_port = SERVER_PORT.to_bytes(2, byteorder='big')

    offer_packet = magic_cookie + message_type + server_name + server_port
    return offer_packet


def send_welcome_message(client_info):
    # Create a TCP socket for sending messages
    try:
        # Send the welcome message
        welcome_message = f"Welcome, {client_info[0]}! The game is starting."
        client_info[1].sendall(welcome_message.encode())

    except Exception as e:
        print(f"Error sending welcome message to {client_info[0]}: {e}")


def start_game():
    global StopOffer
    global StopListen
    StopOffer = True
    StopListen = True
    for client_info in clients_information:
        send_welcome_message(client_info)
    # StopOffer = False
    # StopListen = False


if __name__ == "__main__":
    server()
