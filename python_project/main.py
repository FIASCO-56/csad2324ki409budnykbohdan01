import serial
import time
import threading
import xml.etree.ElementTree as ET
import os

CONFIG_FILE = 'config/game_config.xml'


def setup_serial_port():
    """!
    @brief Sets up the serial port for communication.
    @details Prompts the user to enter the serial port name and configures the port
             with a baud rate of 9600 and a timeout of 1 second.
    @return Configured serial.Serial object.
    """
    try:
        port = input("Enter the serial port (e.g., /dev/ttyUSB0 or COM3): ")
        return serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        exit(1)


def send_message(message, ser):
    """!
    @brief Sends a message through the serial port.
    @details Encodes the message as bytes and writes it to the serial port.
    @param message The string message to send.
    @param ser The serial port object to send the message through.
    """
    try:
        ser.write((message + '\n').encode())
    except serial.SerialException as e:
        print(f"Error sending message: {e}")


def receive_message(ser):
    """!
    @brief Receives a single message from the serial port.
    @details Reads a line of input from the serial port, decodes it to UTF-8, and strips whitespace.
    @param ser The serial port object to read from.
    @return The received string message or None if an error occurs.
    """
    try:
        received = ser.readline().decode('utf-8', errors='ignore').strip()
        if received:
            print(received)
        return received
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None


def receive_multiple_messages(ser, count):
    """!
    @brief Receives multiple messages from the serial port.
    @details Reads a specified number of messages from the serial port and stores them in a list.
    @param ser The serial port object to read from.
    @param count The number of messages to receive.
    @return A list of received messages.
    """
    messages = []
    for _ in range(count):
        message = receive_message(ser)
        if message:
            messages.append(message)
    return messages


def user_input_thread(ser):
    """!
    @brief Handles user input in a separate thread.
    @details Reads commands from the user, processes 'exit' and 'load' commands, and sends messages to the serial port.
    @param ser The serial port object to communicate with.
    """
    global can_input
    while True:
        if can_input:
            user_message = input()
            if user_message.lower() == 'exit':
                print("Exiting...")
                global exit_program
                exit_program = True
                break
            elif user_message.lower().startswith('load'):
                file_path = input("Enter the path to the configuration file: ")
                load_game_config(file_path, ser)
            send_message(user_message, ser)
            can_input = False


def monitor_incoming_messages(ser):
    """!
    @brief Monitors incoming messages from the serial port.
    @details Continuously reads messages, updates the last received time, and saves XML configurations.
    @param ser The serial port object to monitor.
    """
    global can_input
    global last_received_time
    while not exit_program:
        received = receive_message(ser)
        if received:
            last_received_time = time.time()
            if not can_input:
                can_input = True
            if received.startswith("<"):
                print(f"Received XML: {received}")
                save_game_config(received)


def save_game_config(message):
    """!
    @brief Saves a game configuration message to an XML file.
    @details Writes the received XML message to a predefined file location.
    @param message The XML string to save.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(message)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def load_game_config(file_path, ser):
    """!
    @brief Loads a game configuration from an XML file and sends it through the serial port.
    @details Parses the XML file, extracts game settings, and sends them as an XML string.
    @param file_path The path to the XML configuration file.
    @param ser The serial port object to send the configuration through.
    """
    try:
        if os.path.exists(file_path):
            tree = ET.parse(file_path)
            root = tree.getroot()

            game_mode = int(root.find("GameMode").text) if root.find("GameMode") is not None else 0
            player1_symbol = root.find("Player1Symbol").text if root.find("Player1Symbol") is not None else "X"
            player2_symbol = root.find("Player2Symbol").text if root.find("Player2Symbol") is not None else "O"

            print(f"Game Mode: {game_mode}")
            print(f"Player 1 Symbol: {player1_symbol}")
            print(f"Player 2 Symbol: {player2_symbol}")

            xml_message = f"<GameConfig><GameMode>{game_mode}</GameMode>"
            xml_message += f"<Player1Symbol>{player1_symbol}</Player1Symbol>"
            xml_message += f"<Player2Symbol>{player2_symbol}</Player2Symbol></GameConfig>"

            print(xml_message)

            send_message(xml_message, ser)
        else:
            print("Configuration file not found. Please provide a valid path.")
    except Exception as e:
        print(f"Error loading configuration: {e}")


if __name__ == "__main__":
    """!
    @brief Entry point for the serial communication program.
    @details Sets up the serial port, starts threads for monitoring messages and handling user input, 
             and keeps the main thread active until the program exits.
    """
    ser = setup_serial_port()
    can_input = True
    exit_program = False
    last_received_time = time.time()

    threading.Thread(target=monitor_incoming_messages, args=(ser,), daemon=True).start()
    threading.Thread(target=user_input_thread, args=(ser,), daemon=True).start()

    try:
        while not exit_program:
            if time.time() - last_received_time >= 1 and can_input:
                pass
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exit!")
    finally:
        if ser.is_open:
            print("Closing serial port...")
            ser.close()
