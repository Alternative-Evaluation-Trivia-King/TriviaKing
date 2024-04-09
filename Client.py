import random
import socket
import threading

'''----------------------------------------- Global variable --------------------------------------------------'''

BROADCAST_PORT = 13117
names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah", "Isaac", "Julia", "Kevin", "Linda",
         "Michael", "Nancy", "Olivia"]
client_UDP = 0
client_TCP = 0

def client():
    global client_UDP, client_TCP

    try:
        # Create a UDP socket
        client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Bind the socket to the Broadcast
        client_UDP.bind(('0.0.0.0', BROADCAST_PORT))

        print("Client started, listening for offer requests...")

    except KeyboardInterrupt:
        print("Client shutting down...")
        return

    except OSError as e:
        print(f"Error creating or binding UDP socket: {e}")
        if client_UDP is not None:
            client_UDP.close()
        return

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
            clientPlay()
            break

        except KeyboardInterrupt:
            print("Client shutting down...")
            if client_TCP is not None:
                client_TCP.close()
            break

        except OSError as e:
            print(f"Error creating or binding TCP socket: {e}")
            if client_TCP is not None:
                client_TCP.close()

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


def Answer_The_Question(client_TCP):

    while True:
        answer = input("")

        if answer in ['Y', 'T', '1', 'N', 'F', '0']:
            client_TCP.sendall(answer.encode())
            break

        else:
            print("Invalid input\n")


def clientPlay():
    global client_TCP
    try:
        message = client_TCP.recv(1024).decode('utf-8')
        print(message)

        while True:
            message = client_TCP.recv(1024).decode('utf-8')
            print(message)

            if "Game over!" in message:
                client_TCP.close()
                break

            Answer_Question_Thread = threading.Thread(target=Answer_The_Question, args=(client_TCP,), daemon=True)
            Answer_Question_Thread.start()

        print("Server disconnected, listening for offer requests...")

    except ConnectionResetError:
        print("Connection with server reset by peer.")
        client_TCP.close()

    except KeyboardInterrupt:
        print("Client shutting down...")
        if client_TCP is not None:
            client_TCP.close()


if __name__ == "__main__":
    while True:
        client()
