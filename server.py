import socket
import threading
import random
import time
import tkinter as tk
from tkinter import messagebox

# Generate a Bingo number pool (1 to 25)
BINGO_POOL = list(range(1, 26))
random.shuffle(BINGO_POOL)

clients = []  # List of tuples (client_socket, player_number)
lock = threading.Lock()
game_over = False
required_players = 0  # Number of players required to start the game
server_socket = None
winner_player_number = None  # Variable to store the winner's player number

def broadcast(message):
    """Send a message to all connected clients."""
    lock.acquire()
    for client_socket, player_number in clients:
        try:
            client_socket.sendall(message.encode())
        except Exception as e:
            print(f"Error sending message to Player {player_number}: {e}")
    lock.release()

def handle_client(client_socket, player_number, gui):
    """Handle communication with a single client."""
    global game_over, winner_player_number
    while True:
        try:
            # Receive the client's message
            message = client_socket.recv(1024).decode()
            if message == 'BINGO':
                broadcast(f"Player {player_number} has called BINGO!")
                gui.update_status(f"Player {player_number} has won the game!")
                winner_player_number = player_number  # Store the winner's player number
                game_over = True  # Stop the game
                break
        except Exception as e:
            print(f"Error handling Player {player_number}: {e}")
            break

    lock.acquire()
    clients.remove((client_socket, player_number))
    lock.release()
    client_socket.close()

def accept_clients(gui):
    """Accept clients and start threads to handle them."""
    global game_over
    player_number = 1  # Start with Player 1

    while len(BINGO_POOL) > 0 and not game_over:
        try:
            client_socket, addr = server_socket.accept()
            gui.update_status(f"New client connected from {addr} as Player {player_number}")

            # Add the client and assign a player number
            lock.acquire()
            clients.append((client_socket, player_number))
            lock.release()

            gui.update_players(len(clients))

            # Start a thread to handle the client, passing the player number
            client_thread = threading.Thread(target=handle_client, args=(client_socket, player_number, gui))
            client_thread.start()

            # Increment the player number for the next player
            player_number += 1
        except OSError:
            # Server socket may have been closed after the game ended
            break

    gui.update_status("No longer accepting clients. Game has ended or the server socket is closed.")

def server(gui):
    global game_over, required_players, server_socket, winner_player_number
    game_over = False
    winner_player_number = None  # Reset the winner before the game starts

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 12345))  # Bind to all IPs, port 12345
    server_socket.listen(5)
    gui.update_status("Bingo Server Started...")

    try:
        required_players = int(gui.required_players_input.get())
    except ValueError:
        gui.update_status("Invalid number of players! Please enter a valid number.")
        return

    gui.update_status(f"Waiting for {required_players} players to join...")

    # Start accepting clients in a separate thread
    accept_thread = threading.Thread(target=accept_clients, args=(gui,))
    accept_thread.start()

    # Wait until the required number of players have connected
    while len(clients) < required_players and not game_over:
        time.sleep(1)  # Wait before checking again

    if game_over:
        gui.update_status("Game ended before starting.")
        server_socket.close()
        return

    gui.update_status(f"All {required_players} players connected! Starting the game.")

    # Start broadcasting Bingo numbers to clients
    while len(BINGO_POOL) > 0 and not game_over:
        if len(clients) > 0:  # Only broadcast if there are active clients
            # Send the next Bingo number
            number = BINGO_POOL.pop(0)
            broadcast(f"New Bingo number: {number}")
            gui.update_bingo_number(f"Number {number} sent to all clients")

            # Delay between number broadcasts
            time.sleep(5)  # 5 seconds delay between numbers
        else:
            gui.update_status("No active clients. Waiting for a client to join.")
            time.sleep(1)  # Check again after 1 second

    if game_over:
        gui.update_status("Game Over! A player has won.")
        if winner_player_number:
            gui.display_winner(winner_player_number)  # Display the winner on the GUI
    else:
        gui.update_status("Game Over! No more numbers.")

    # Close the server socket after the game is over
    server_socket.close()

class BingoGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bingo Server")

        # Create the main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)

        # Players required input
        self.required_players_label = tk.Label(self.main_frame, text="Enter the number of players required to start:")
        self.required_players_label.pack()

        self.required_players_input = tk.Entry(self.main_frame)
        self.required_players_input.pack()

        # Start server button
        self.start_button = tk.Button(self.main_frame, text="Start Server", command=self.start_server)
        self.start_button.pack(pady=5)

        # Status display
        self.status_label = tk.Label(self.main_frame, text="Game Status:", font=("Helvetica", 14))
        self.status_label.pack()

        self.status_display = tk.Text(self.main_frame, height=10, width=50, state=tk.DISABLED)
        self.status_display.pack()

        # Bingo number display
        self.bingo_number_label = tk.Label(self.main_frame, text="Current Bingo Number:", font=("Helvetica", 12))
        self.bingo_number_label.pack()

        self.bingo_number_display = tk.Label(self.main_frame, text="---", font=("Helvetica", 20))
        self.bingo_number_display.pack()

        # Player count display
        self.players_connected_label = tk.Label(self.main_frame, text="Players Connected:", font=("Helvetica", 12))
        self.players_connected_label.pack()

        self.players_connected_display = tk.Label(self.main_frame, text="0", font=("Helvetica", 20))
        self.players_connected_display.pack()

    def start_server(self):
        # Start the server in a separate thread
        server_thread = threading.Thread(target=server, args=(self,))
        server_thread.start()

    def update_status(self, message):
        self.status_display.config(state=tk.NORMAL)
        self.status_display.insert(tk.END, message + "\n")
        self.status_display.see(tk.END)
        self.status_display.config(state=tk.DISABLED)

    def update_bingo_number(self, number):
        self.bingo_number_display.config(text=number)

    def update_players(self, count):
        self.players_connected_display.config(text=str(count))

    def display_winner(self, player_number):
        """Update the GUI to show the winner."""
        self.bingo_number_label.config(text="Winner!")
        self.bingo_number_display.config(text=f"Player {player_number}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = BingoGUI(root)
    root.mainloop()
