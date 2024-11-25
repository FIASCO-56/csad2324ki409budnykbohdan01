import serial
import time
import threading
import xml.etree.ElementTree as ET
import os

CONFIG_FILE = 'config/game_config.xml'


def setup_serial_port():
    try:
        port = input("Enter the serial port (e.g., /dev/ttyUSB0 or COM3): ")
        return serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        exit(1)


def send_message(message, ser):
    try:
        ser.write((message + '\n').encode())
    except serial.SerialException as e:
        print(f"Error sending message: {e}")


def receive_message(ser):
    try:
        received = ser.readline().decode('utf-8', errors='ignore').strip()
        if received:
            print(received)
        return received
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None


def receive_multiple_messages(ser, count):
    messages = []
    for _ in range(count):
        message = receive_message(ser)
        if message:
            messages.append(message)
    return messages


def user_input_thread(ser):
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
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(message)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def load_game_config(file_path, ser):
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
