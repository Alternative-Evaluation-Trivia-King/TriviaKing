import random
import socket
import time
#import keyboard

'''----------------------------------------- Global variable --------------------------------------------------'''

BROADCAST_PORT = 13117
names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah", "Isaac", "Julia", "Kevin", "Linda",
         "Michael", "Nancy", "Olivia"]
flagValidInput = False
flagTimeoutToInput = False


def client():
    # Create a UDP socket
    client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind the socket to the Broadcast
    client_UDP.bind(('0.0.0.0', BROADCAST_PORT))

    print("Client started, listening for offer requests...")

    while True:
        try:
            # Receives data from the server over the UDP socket and stores the received data
            data, server_address = client_UDP.recvfrom(1024)

            # Extract packet from server
            server_name, server_port, isValid = ExtractPacketFromServer(data)
            if not isValid:
                continue

            print(f"Received offer from server {server_name} at address {server_address[0]}, attempting to connect...")

            # Connect to the server over TCP
            client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Establishes a connection for client sockets to a remote server.
            client_TCP.connect((server_address[0], server_port))
            print("Connected to server over TCP.")

            # Choose a name randomly
            player_name = random.choice(names)
            # Send the name to the server
            client_TCP.sendall(player_name.encode() + b'\n')

            # Start play
            clientPlay(client_TCP)

        except KeyboardInterrupt:
            print("Client shutting down...")
            break

    # Close the UDP socket
    client_UDP.close()


def ExtractPacketFromServer(data):
    isValid = True
    magic_cookie = int.from_bytes(data[:4], byteorder='big')
    message_type = int.from_bytes(data[4:5], byteorder='big')
    server_name = data[5:37].decode('utf-8').strip('\x00')
    server_port = int.from_bytes(data[37:39], byteorder='big')

    if magic_cookie != 0xabcddcba or message_type != 0x2:
        print("The received package does not meet certain criteria")
        isValid = False

    return server_name, server_port, isValid


def clientPlay(client_TCP):
    global flagValidInput, flagTimeoutToInput

    def on_key_press(event):
        global flagValidInput
        if event.name in ['Y', 'T', '1', 'N', 'F', '0']:
            # Send the user's choice to the server
            client_TCP.sendall(event.name.encode())
            flagValidInput = True

        else:
            print("Invalid input")

    message = client_TCP.recv(1024).decode('utf-8')
    print(message)
    # Register the key press listener
    keyboard.on_press(on_key_press)
    while True:
        timeToEnterInput = 10
        question = client_TCP.recv(1024).decode('utf-8')
        print(question)
        # Block the main thread to keep listening for key presses

        while not flagTimeoutToInput and not flagValidInput:
            startTime = time.time()
            keyboard.wait(timeToEnterInput)
            timeToEnterInput = timeToEnterInput - (time.time() - startTime)
            if timeToEnterInput <= 0:
                flagTimeoutToInput = False


if __name__ == "__main__":
    client()
