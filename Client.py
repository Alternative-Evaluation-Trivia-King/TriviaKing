import random
import socket
import threading
import time

'''----------------------------------------- Global variable --------------------------------------------------'''

'''
This class represents the client that should play on the server.
You can create as many clients as you want.
'''


class Client:
    def __init__(self):
        self.client_UDP = 0
        self.client_TCP = 0
        self.BROADCAST_PORT = 13117
        self.names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah", "Isaac", "Julia", "Kevin",
                      "Linda",
                      "Michael", "Nancy", "Olivia"]

    '''
    This method represents the entire beginning of the client's interaction with the server.
    From the moment it creates a UDP connection, a TCP connection to the moment it plays.
    '''
    def startClient(self):
        try:
            self.client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.client_UDP.bind(('0.0.0.0', self.BROADCAST_PORT))
            print("Client started, listening for offer requests...")

        except OSError as e:
            print(f"Error creating or binding UDP socket: {e}")
            if self.client_UDP is not None:
                self.client_UDP.close()
            return

        while True:
            try:
                data, server_address = self.client_UDP.recvfrom(1024)
                server_name, server_port, isValid = self.ExtractPacketFromServer(data)
                if not isValid:
                    continue

                print(f"Received offer from server {server_name} at address {server_address[0]}, attempting to connect...")
                self.client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_TCP.connect((server_address[0], server_port))
                print("Connected to server over TCP.")
                player_name = random.choice(self.names)
                self.client_TCP.sendall(player_name.encode() + b'\n')

                self.clientPlay()
                break

            except OSError as e:
                print(f"Error creating or binding TCP socket: {e}")
                if self.client_TCP is not None:
                    self.client_TCP.close()

            except KeyboardInterrupt:
                print("Force quit detected. Closing connections...")
                if self.client_TCP:
                    self.client_TCP.close()
                if self.client_UDP:
                    self.client_UDP.close()
                break

        if self.client_UDP:
            self.client_UDP.close()

    '''
    The function of this method is to extract the data from the packet
    that represents the invitation to the game from the server side.
    '''
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

    '''
    This method belongs to Tread,
    whose entire function is to handle the client's answer to the server's question,
    and send the final answer to the server.
    '''

    def Answer_The_Question(self):
        while True:
            try:
                answer = input("")
                self.client_TCP.sendall(answer.encode())

            except UnicodeDecodeError:
                print("Error: Unable to decode input. Please try again with valid characters.")

    '''
    This method represents the game of the client against the server.
    This method waits for questions and also answers the questions.
    '''
    def clientPlay(self):
        try:
            while True:
                message = self.client_TCP.recv(1024).decode('utf-8')
                print(message)

                if "Welcome" in message:
                    continue

                if "Game over!" in message:
                    self.client_TCP.close()
                    break

                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question, daemon=True)
                Answer_Question_Thread.start()

            print("\nServer disconnected, listening for offer requests...\n")



        except ConnectionResetError:
            print("Connection with server reset by peer.")
            self.client_TCP.close()


if __name__ == "__main__":
    client = Client()
    while True:
        client.startClient()
