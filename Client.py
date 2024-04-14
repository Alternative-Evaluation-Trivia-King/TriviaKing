import random
import socket
import threading


# ------------------------------------------ Helper function ------------------------------------------------

'''
This function extracts relevant information from the packet received from the server.
It parses the packet to retrieve the server's name, port, and validates the packet's integrity.
'''
def ExtractPacketFromServer(data):
    isRelevantPacket = True
    # Extract the magic cookie from the first 4 bytes of the data and convert it to an integer
    magic_cookie = int.from_bytes(data[:4], byteorder='big')
    # Extract the message type from the 5th byte of the data and convert it to an integer
    message_type = int.from_bytes(data[4:5], byteorder='big')
    # Decode the server name from bytes 6 to 37, remove any null characters, and convert it to a string
    server_name = data[5:37].decode('utf-8').strip('\x00')
    # Extract the server port from bytes 38 to 39 and convert it to an integer
    server_port = int.from_bytes(data[37:39], byteorder='big')

    # Check if the magic cookie and message type meet certain criteria
    if magic_cookie != 0xabcddcba or message_type != 0x2:
        print("The received package does not meet certain criteria")
        isRelevantPacket = False

    return server_name, server_port, isRelevantPacket

def print_with_color(message, color='\033[31m'):
    print(color + message + '\033[0m')

# ------------------------------------------ Client class ------------------------------------------------

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
            # Create a UDP socket
            self.client_UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Allow reusing addresses
            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Enable broadcasting
            self.client_UDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Bind the socket to listen on all available interfaces (0.0.0.0)
            self.client_UDP.bind(('0.0.0.0', self.BROADCAST_PORT))
            print("Client started, listening for offer requests...")

        except OSError as e:
            print_with_color(f"Error creating or binding UDP socket: {e}")
            if self.client_UDP is not None:
                self.client_UDP.close()
            return

        # Continuously listen for offer requests and establish TCP connection
        while True:
            try:
                # Wait to receive data from the UDP socket
                data, server_address = self.client_UDP.recvfrom(1024)
                # Extract server information from the received data
                server_name, server_port, isRelevantPacket = ExtractPacketFromServer(data)
                # If the received packet is not valid, continue listening
                if not isRelevantPacket:
                    continue

                print(f"Received offer from server {server_name} at address {server_address[0]}, attempting to connect...")
                # Create a TCP socket for establishing a connection with the server
                self.client_TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # Connect to the server over TCP using its address and port
                self.client_TCP.connect((server_address[0], server_port))
                print("Connected to server over TCP.")

                # Send a random player name to the server
                player_name = random.choice(self.names)
                self.client_TCP.sendall(player_name.encode() + b'\n')

                # Start playing the game
                # self.clientPlay()
                break

            except OSError as e:
                print_with_color(f"Error creating or binding TCP socket: {e}")
                if self.client_TCP is not None:
                    self.client_TCP.close()

        # Close the UDP socket after use
        if self.client_UDP:
            self.client_UDP.close()

    '''
    This method handles the client's response to the server's questions during gameplay.
    It continuously prompts the user for input and sends the entered answer to the server.
    '''
    def Answer_The_Question(self):
        while True:
            try:
                # Prompt the client for input
                answer = input("")
                # Send the answer to the server
                self.client_TCP.sendall(answer.encode())

            except UnicodeDecodeError:
                print_with_color("Error: Unable to decode input. Please try again with valid characters.")

    '''
    This method represents the gameplay loop for the client.
    It receives messages from the server, displays them to the user,and prompts for responses.
    Additionally, it handles the threading for input handling,
    allowing simultaneous communication with the server.
    '''
    def clientPlay(self):
        try:
            while True:
                # Receive messages from the server
                message = self.client_TCP.recv(1024).decode('utf-8')
                print(message)

                if "Welcome" in message:
                    continue

                # Break the loop if the message contains "Game over!"
                if "Game over!" in message:
                    self.client_TCP.close()
                    break

                # Start a thread for handling user input
                Answer_Question_Thread = threading.Thread(target=self.Answer_The_Question, daemon=True)
                Answer_Question_Thread.start()

            print("\nServer disconnected, listening for offer requests...\n")

        # Handling the case where the connection with the server crashes
        except ConnectionResetError:
            print_with_color("Connection with the server crashed.")
            self.client_TCP.close()


if __name__ == "__main__":
    client = Client()
    while True:
        client.startClient()
        client.clientPlay()
