import socket
import random
import threading
import tkinter as tk
from tkinter import scrolledtext

def generate_bingo_card():
    numbers = random.sample(range(1, 26), 25)
    card = [numbers[i:i + 5] for i in range(0, 25, 5)]
    return card

class BingoClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Bingo Client")

        # Bingo card frame
        self.card_frame = tk.Frame(self.root)
        self.card_frame.pack(pady=10)

        self.card_label = tk.Label(self.card_frame, text="Your Bingo Card:")
        self.card_label.pack()

        # Create a Canvas to draw the Bingo card
        self.card_canvas = tk.Canvas(self.card_frame, width=300, height=300)
        self.card_canvas.pack()
        self.card_canvas.bind("<Button-1>", self.on_canvas_click)

        # Status frame for displaying numbers and progress
        self.status_frame = tk.Frame(self.root)
        self.status_frame.pack(pady=10)

        self.status_label = tk.Label(self.status_frame, text="Status Updates:")
        self.status_label.pack()

        self.status_display = scrolledtext.ScrolledText(self.status_frame, height=8, width=50, state=tk.DISABLED)
        self.status_display.pack()

        # Connect to server button
        self.connect_button = tk.Button(self.root, text="Connect to Server", command=self.start_client)
        self.connect_button.pack(pady=10)

        # Initialize the bingo card and marking
        self.bingo_card = generate_bingo_card()
        self.marked = [[False] * 5 for _ in range(5)]
        self.called_numbers = []  # List to track all announced numbers
        self.update_card_display()

    def update_card_display(self):
        """Update the Bingo card display in the Canvas widget."""
        self.card_canvas.delete("all")  # Clear the canvas
        for i in range(5):
            for j in range(5):
                x0 = j * 60 + 10
                y0 = i * 60 + 10
                x1 = x0 + 50
                y1 = y0 + 50
                number = self.bingo_card[i][j]
                text = "X" if self.marked[i][j] else str(number)

                # Draw rectangle for the Bingo number
                self.card_canvas.create_rectangle(x0, y0, x1, y1, fill="white")
                # Draw the number or 'X'
                self.card_canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=text, font=("Helvetica", 16))

    def update_status(self, message):
        """Update the status display with a new message."""
        self.status_display.config(state=tk.NORMAL)
        self.status_display.insert(tk.END, message + "\n")
        self.status_display.yview(tk.END)  # Auto-scroll
        self.status_display.config(state=tk.DISABLED)

    def listen_for_numbers(self, sock):
        """Listen for Bingo numbers from the server in a separate thread."""
        while True:
            try:
                message = sock.recv(1024).decode()
                if "New Bingo number" in message:
                    number = int(message.split(": ")[1])
                    self.called_numbers.append(number)  # Add the new number to called numbers
                    self.update_status(f"Bingo number received: {number}")

                    # Check how many lines have been completed
                    lines_completed = check_bingo(self.marked)
                    self.update_status(f"Lines completed: {lines_completed}")

                    # Call Bingo if 5 lines (rows, columns, or diagonals) are completed
                    if lines_completed >= 5:
                        self.update_status("BINGO! You won!")
                        sock.sendall("BINGO".encode())
                        break
                elif "BINGO" in message:
                    self.update_status(message)  # Announce if someone else wins
                    break
            except Exception as e:
                self.update_status(f"Error receiving data: {e}")
                break

    def on_canvas_click(self, event):
        """Mark a Bingo number as 'X' when clicked."""
        # Get the position of the click
        x = event.x
        y = event.y

        # Determine the row and column of the clicked number
        row = y // 60
        col = x // 60

        # Check if the click is within the Bingo card range
        if 0 <= row < 5 and 0 <= col < 5:
            number = self.bingo_card[row][col]
            # Only mark if the number has been announced
            if not self.marked[row][col] and number in self.called_numbers:
                self.marked[row][col] = True
                self.update_card_display()
                self.update_status(f"Marked number {number} as 'X'.")

                # Check how many lines have been completed after marking
                lines_completed = check_bingo(self.marked)
                if lines_completed >= 5:
                    self.update_status("BINGO! You won!")
                    # Optionally, send the BINGO message to the server
                    # sock.sendall("BINGO".encode())

    def start_client(self):
        """Start the Bingo client connection to the server."""
        self.update_status("Connecting to the Bingo server...")

        # Connect to the Bingo server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(('192.168.5.238', 12345))
            self.update_status("Connected to the server.")

            # Start listening for Bingo numbers
            listen_thread = threading.Thread(target=self.listen_for_numbers, args=(sock,))
            listen_thread.start()
        except Exception as e:
            self.update_status(f"Failed to connect: {e}")

def check_bingo(marked):
    """Check how many rows, columns, or diagonals are completely marked."""
    lines_completed = 0

    # Check rows
    for row in marked:
        if all(row):
            lines_completed += 1

    # Check columns
    for col in range(5):
        if all(marked[row][col] for row in range(5)):
            lines_completed += 1

    # Check diagonals
    if all(marked[i][i] for i in range(5)):
        lines_completed += 1
    if all(marked[i][4 - i] for i in range(5)):
        lines_completed += 1

    return lines_completed

if __name__ == "__main__":
    root = tk.Tk()
    gui = BingoClientGUI(root)
    root.mainloop()
