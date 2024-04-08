import socket
import time
import threading

# Server configuration
BROADCAST_PORT = 13117
SERVER_IP = "172.1.0.4"  # Change this to the desired server IP address
client_names = []


def server():
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
    # tcp_server_socket.listen()  # Listen for incoming connections

    while True:
        try:
            # Accept incoming client connection
            client_socket, _ = tcp_server_socket.accept()

            # Receive player name from client
            player_name = client_socket.recv(1024).decode().strip()
            client_names.append(player_name)

            # Close the client socket
            client_socket.close()

        except KeyboardInterrupt:
            print("Listening thread shutting down...")
            break


def send_offer_announcements(server_socket, SERVER_PORT):
    while True:
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
    SERVER_PORT = 5000
    while True:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            server_socket.bind((SERVER_IP, SERVER_PORT))
            return SERVER_PORT, server_socket

        except OSError as e:
            SERVER_PORT += 1


def craft_offer_packet(SERVER_PORT):
    # Craft the offer announcement packet
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name = "MyServer".ljust(32, '\x00').encode('utf-8')
    server_port = SERVER_PORT.to_bytes(2, byteorder='big')

    offer_packet = magic_cookie + message_type + server_name + server_port
    return offer_packet
