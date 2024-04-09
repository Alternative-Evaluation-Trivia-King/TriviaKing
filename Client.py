import random
import socket
import threading

'''----------------------------------------- Global variable --------------------------------------------------'''


class Client:
    def __init__(self):
        self.client_UDP = 0
        self.client_TCP = 0
        self.BROADCAST_PORT = 13117
        self.names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah", "Isaac", "Julia", "Kevin", "Linda",
                 "Michael", "Nancy", "Olivia"]

    def startClient(self):
        try:
            # Create a UDP socket
            self.client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Bind the socket to the Broadcast
            self.client_UDP.bind(('0.0.0.0', self.BROADCAST_PORT))

            print("Client started, listening for offer requests...")

        except KeyboardInterrupt:
            print("Client shutting down...")
            return

        except OSError as e:
            print(f"Error creating or binding UDP socket: {e}")
            if self.client_UDP is not None:
                self.client_UDP.close()
            return

        while True:
            try:
                # Receives data from the server over the UDP socket and stores the received data
                data, server_address = self.client_UDP.recvfrom(1024)

                # Extract packet from server
                server_name, server_port, isValid = self.ExtractPacketFromServer(data)
                if not isValid:
                    continue

                print(f"Received offer from server {server_name} at address {server_address[0]}, attempting to connect...")

                # Connect to the server over TCP
                self.client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Establishes a connection for client sockets to a remote server.
                self.client_TCP.connect((server_address[0], server_port))
                print("Connected to server over TCP.")

                # Choose a name randomly
                player_name = random.choice(self.names)
                # Send the name to the server
                self.client_TCP.sendall(player_name.encode() + b'\n')

                # Start play
                self.clientPlay()
                break

            except KeyboardInterrupt:
                print("Client shutting down...")
                if self.client_TCP is not None:
                    self.client_TCP.close()
                break

            except OSError as e:
                print(f"Error creating or binding TCP socket: {e}")
                if self.client_TCP is not None:
                    self.client_TCP.close()

        # Close the UDP socket
        self.client_UDP.close()


    def ExtractPacketFromServer(self, data):
        isValid = True
        magic_cookie = int.from_bytes(data[:4], byteorder='big')
        message_type = int.from_bytes(data[4:5], byteorder='big')
        server_name = data[5:37].decode('utf-8').strip('\x00')
        server_port = int.from_bytes(data[37:39], byteorder='big')

        if magic_cookie != 0xabcddcba or message_type != 0x2:
            print("The received package does not meet certain criteria")
            isValid = False

        return server_name, server_port, isValid


    def Answer_The_Question(self):

        while True:
            answer = input("")

            if answer in ['Y', 'T', '1', 'N', 'F', '0']:
                self.client_TCP.sendall(answer.encode())
                break

            else:
                print("Invalid input\n")


    def clientPlay(self):
        try:
            message = self.client_TCP.recv(1024).decode('utf-8')
            print(message)

            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')
                print(message)

                if "Game over!" in message:
                    self.client_TCP.close()
                    break

                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question, daemon=True)
                Answer_Question_Thread.start()

            print("Server disconnected, listening for offer requests...")

        except ConnectionResetError:
            print("Connection with server reset by peer.")
            self.client_TCP.close()

        except KeyboardInterrupt:
            print("Client shutting down...")
            if self.client_TCP is not None:
                self.client_TCP.close()


if __name__ == "__main__":
    client = Client()
    while True:
        client.startClient()
