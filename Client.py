import random
import socket
import threading


'''
This class facilitates the interaction of a client with a server for multiplayer gaming purposes.
It's intended for creating multiple client instances that can connect to a server simultaneously.
This class provides a robust framework for implementing multiplayer game clients that can connect to a server,
exchange messages, and participate in gameplay.
'''
class Client:
    """
    The __init__ method initializes a Client object with the following attributes:
    - client_UDP: Represents the UDP socket for communication with the server.
    - client_TCP: Represents the TCP socket for communication with the server.
    - BROADCAST_PORT: The port number used for broadcasting UDP packets.
    - names: A list of names that can be randomly assigned to the client during gameplay.
    """
    def __init__(self):
        self.client_UDP = 0
        self.client_TCP = 0
        self.BROADCAST_PORT = 13117
        self.names = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Hannah",
                      "Isaac", "Julia", "Kevin", "Linda", "Michael", "Nancy", "Olivia"]

    '''
    This method is responsible for the entire interaction process between the client and the server.
    It starts by establishing a UDP connection to listen for offer requests from the server.
    Upon receiving a valid offer, it establishes a TCP connection with the server.
    After connecting, it continues to play the game.
    '''
    def startClient(self):
        try:
            # Create and bind a UDP socket for receiving server offers
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

        # Continuously listen for offer requests and establish TCP connection
        while True:
            try:
                data, server_address = self.client_UDP.recvfrom(1024)
                server_name, server_port, isValid = self.ExtractPacketFromServer(data)
                if not isValid:
                    continue

                print(f"Received offer from server {server_name} at address {server_address[0]}, attempting to connect...")
                # Connect to the server over TCP
                self.client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_TCP.connect((server_address[0], server_port))
                print("Connected to server over TCP.")

                # Send a random player name to the server
                player_name = random.choice(self.names)
                self.client_TCP.sendall(player_name.encode() + b'\n')

                # Start playing the game
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

        # Close the UDP socket after use
        if self.client_UDP:
            self.client_UDP.close()

    '''
    This method extracts relevant information from the packet received from the server.
    It parses the packet to retrieve the server's name, port, and validates the packet's integrity.
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
    This method handles the client's response to the server's questions during gameplay.
    It continuously prompts the user for input and sends the entered answer to the server.
    '''
    def Answer_The_Question(self):
        while True:
            try:
                answer = input("")
                self.client_TCP.sendall(answer.encode())

            except UnicodeDecodeError:
                print("Error: Unable to decode input. Please try again with valid characters.")

    '''
    This method represents the gameplay loop for the client.
    It receives messages from the server, displays them to the user,and prompts for responses.
    Additionally, it handles the threading for input handling,
    allowing simultaneous communication with the server.
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

                # Start a thread for handling user input
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
