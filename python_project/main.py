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
    @brief Loads the game configuration from a file and sends it over serial.
    @param file_path The path to the configuration file to load.
    @param ser The serial.Serial object for communication.
    @details This function reads the content of the configuration file and sends it over the serial port.
    @exception Will print an error message if the file cannot be loaded.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                xml_content = f.read()

            print("Loaded XML content:")
            print(xml_content)

            send_message(xml_content, ser)
        else:
            print("Configuration file not found. Please provide a valid path.")
    except Exception as e:
        print(f"Error loading configuration: {e}")


def main():
    """!
    @brief Main function to initialize serial communication and handle threads.
    @details This function sets up the serial communication, starts the threads for monitoring incoming messages and handling user input, and manages the program loop.
    """
    global can_input, exit_program  # Ensure variables are accessible in tests
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

if __name__ == "__main__":
    main()
