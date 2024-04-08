import random
import socket

# Server configuration
BROADCAST_PORT = 13117
names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah", "Isaac", "Julia", "Kevin", "Linda", "Michael", "Nancy", "Olivia"]

def client():
    # Create a UDP socket
    client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Bind the socket to the server address and port
    client_UDP.bind(('0.0.0.0', BROADCAST_PORT))

    print("Client started, listening for offer requests...")

    while True:
        try:
            data, server_address = client_UDP.recvfrom(1024)
            magic_cookie = int.from_bytes(data[:4], byteorder='big')
            message_type = int.from_bytes(data[4:5], byteorder='big')
            server_name = data[5:37].decode('utf-8').strip('\x00')  # Assuming the server name is Unicode encoded
            server_port = int.from_bytes(data[37:39], byteorder='big')

            if magic_cookie != 0xabcddcba or message_type != 0x2:
                print("The received package does not meet certain criteria")
                continue

            print("Received offer from server "+server_name+" at address "+server_address[0]+", attempting to connect...")

            # Connect to the server over TCP
            client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_TCP.connect((server_address[0], server_port))
            print("Connected to server over TCP.")

            # Choose a name randomly
            player_name = random.choice(names)
            client_TCP.sendall(player_name.encode() + b'\n')

            clientPlay(client_TCP)

        except KeyboardInterrupt:
            print("Client shutting down...")
            break


    # Close the socket
    client_UDP.close()


def clientPlay(client_TCP):
    message = client_TCP.recv(1024).decode('utf-8')
    print(message)
    while True:
        pass
    # welcome_message = client_TCP.recv(1024).decode()
    # print(welcome_message)

if __name__ == "__main__":
    client()