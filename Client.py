import socket

# Server configuration
BROADCAST_PORT = 13117

def client():
    # Create a UDP socket
    client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    # Bind the socket to the server address and port
    client_UDP.bind(('localhost', BROADCAST_PORT))

    print("Client started, listening for offer requests...")

    while True:
        try:
            data, server_address = client_UDP.recvfrom(1024)
            magic_cookie = int.from_bytes(data[:4], byteorder='big')
            message_type = int.from_bytes(data[4:5], byteorder='big')
            server_name = data[5:37].decode('utf-8').strip('\x00')  # Assuming the server name is Unicode encoded
            server_port = int.from_bytes(data[37:39], byteorder='big')

            if magic_cookie == 0xabcddcba and message_type == 0x2:
                print("The received package does not meet certain criteria")
                continue

            print("Received offer from server "+server_name+" at address "+server_address+", attempting to connect...")

            # Connect to the server over TCP
            client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_TCP.connect((server_address, server_port))
            print("Connected to server over TCP.")

            # Send player name to the server
            player_name = "Alice"  # Change this to the actual player name
            client_TCP.sendall(player_name.encode() + b'\n')

            clientPlay(client_TCP)

        except KeyboardInterrupt:
            print("Client shutting down...")
            break


    # Close the socket
    client_UDP.close()


def clientPlay(client_TCP):
    welcome_message = client_TCP.recv(1024).decode()
    print(welcome_message)