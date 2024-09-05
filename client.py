import socket
import threading
from Crypto.PublicKey import RSA
import base64
import json
import cv2, pickle, struct
from Crypto.Cipher import PKCS1_OAEP
import time
from queue import Queue

QUEUE_SIZE = 15

clients = {}
video_list = []

client_queues = Queue(maxsize=QUEUE_SIZE)

def main_receive(client_socket,private_key,name):
    while True:
        try:
            # Receive the packed size (4 bytes)
            size_packed = client_socket.recv(8)

            # Unpack the size to get the actual size
            data_size = struct.unpack("Q", size_packed)[0]

            # Receive the JSON data
            received_data = b''
            while len(received_data) < data_size:
                chunk = client_socket.recv(min(data_size - len(received_data), 1024))
                if not chunk:
                    break
                received_data += chunk

            # Decode the received JSON data
            received = received_data.decode()
            # received = client_socket.recv(1024).decode()

            update_clients_info(client_socket,received)
            receive_and_decrypt(client_socket, private_key,received)            

            data = json.loads(received)
            # print(data)
            if 'Type' in data:
                if (data["Type"] == "Videos List"):
                    video_list.clear()
                    print("Available videos:")
                    for video in data["Video"]:
                        print(video)
                        video_list.append(video)
                elif(data["Type"] == "Video Start"):
                    receive_video_frames(client_socket, private_key,name)
                elif data['Type'] == "QUIT":
                    print("Client disconnected.")
                    break
            
        except:
            print("Client disconnected.")
            break
    exit(0)  


def establish_connection():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 9999))
    return client_socket

def send_name_and_public_key(client_socket, name, public_key):
    client_socket.send(name.encode())  # Send client name
    client_socket.send(public_key.exportKey().decode().encode())  # Send public key


def secure_communication(client_socket, message, recipient_public_key_str):
    recipient_public_key = RSA.import_key(recipient_public_key_str)
    max_message_size = RSA.import_key(recipient_public_key_str).size_in_bytes() - 42  # Maximum size for RSA encryption

    if len(message.encode()) > max_message_size:
        raise ValueError("Message size exceeds the maximum size that RSA can encrypt")

    cipher = PKCS1_OAEP.new(recipient_public_key)
    encrypted_message = cipher.encrypt(message.encode())
    encoded_message = base64.b64encode(encrypted_message).decode()
    # Create a JSON object containing the encrypted message
    json_data = {
    "Encrypted": True, 
    "encrypted_message": encoded_message
    }
    # Convert the JSON object to a string
    json_string = json.dumps(json_data)
    client_socket.send(json_string.encode())  # Send encrypted message to server
    

def decrypt_message(encrypted_message, client_private_key):
    cipher = PKCS1_OAEP.new(client_private_key)
    decrypted_message = cipher.decrypt(encrypted_message).decode('utf-8')
    # print("Decrypted message:", decrypted_message.decode())
    return decrypted_message


def receive_broadcasted_clients(client_socket,received):
    received_data = received    
    decoded_data = received_data
    
    # Parse the received JSON data
    data = json.loads(decoded_data)
    encoded = data["Encrypted"]
    
    if (not encoded):
    # Check if the data has the expected structure
        if 'Type' in data and 'clients_info' in data:
            broadcast_info = data['Type']
            clients_info_json = data['clients_info']
            
            # Check if the broadcast info matches
            if broadcast_info == "Broadcast":
                # Parse clients' information JSON
                clients_info = clients_info_json
                
                # Update clients dictionary with received information
                for client_name, public_key in clients_info.items():
                    clients[client_name] = public_key.strip()
                
                # Remove clients that are not present in clients_info_json
                clients_to_remove = []
                for client_name in clients:
                    if client_name not in clients_info_json:
                        clients_to_remove.append(client_name)
                
                for client_name in clients_to_remove:
                    del clients[client_name]
                
            else:
                print("Unexpected broadcast info:", broadcast_info)


def update_clients_info(client_socket,received):
    receive_broadcasted_clients(client_socket,received)
    return


def receive_and_decrypt(client_socket, private_key, received):
    # json_string = client_socket.recv(1024).decode()
    json_string = received
    json_data = json.loads(json_string)
    encrypted = json_data["Encrypted"]
    if (encrypted):
        encoded_message = json_data["encrypted_message"]
        # print(encrypted_message)
        encrypted_message = base64.b64decode(encoded_message)
        if encrypted_message:
            data = encrypted_message
            decrypted_message=""
            try:
                decrypted_message = decrypt_message(data, private_key)
            except:
                decrypted_message=""
            if decrypted_message:
                print("Received: \n", decrypted_message, "\n")  # Adding newline character
        else:
            print("Received data does not start with 'Client_Message':")
    return

 
def receive_video_frames(client_socket, private_key,name):
    data = b""
    payload_size = struct.calcsize("Q")
    
    try:
        while True:
            while len(data) < payload_size:
                packet = client_socket.recv(1024)  # 1K buffer size
                if not packet:
                    break
                data += packet
            if not data:
                break
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(data) < msg_size:
                data += client_socket.recv(1024)  # 1K buffer size
            frame_data = data[:msg_size]
            if frame_data == b'done':
                break
            data = data[msg_size:]
            
            # Attempt to load frame data as pickle
            try:
                frame = pickle.loads(frame_data)
            except pickle.UnpicklingError:
                # If not pickle, try loading as JSON
                try:
                    frame_data_json = frame_data.decode()
                    # Process frame data from JSON
                    client_queues.put(frame_data_json)
                    continue
                except json.JSONDecodeError:
                    print("Error decoding JSON data")
                    continue
            
            # Process frame data from pickle (or continue if JSON was processed)
            cv2.imshow(f'Client {name}', frame)
            key = cv2.waitKey(1)
            # if key == ord('q') or key == 27:  # Press 'q' or Esc to quit
            #     break
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cv2.destroyAllWindows()
        handle_backend(client_socket,private_key)
        
def handle_backend(client_socket,private_key):
    while not client_queues.empty():
        data = client_queues.get()
        update_clients_info(client_socket,data)
        receive_and_decrypt(client_socket, private_key, data)


def main():
    client_socket = establish_connection()
    
    is_connected = True
    
    # Generate RSA key pair
    key = RSA.generate(2048)
    public_key = key.publickey()
    print(public_key)
    private_key = key
    
    # Example usage:
    name = input("Enter your name: ")
    send_name_and_public_key(client_socket, name, public_key)

    response = client_socket.recv(1024).decode()
    print(response)
    if response.startswith("Error:"):
        # Close the connection if an error message is received
        print("Closing connection...")
        is_connected = False
        client_socket.close()
    else:
        pass
    
    if is_connected:
        # Example of receiving broadcasted clients info from server
        main_thread = threading.Thread(target=main_receive, args=(client_socket,private_key,name))
        main_thread.start()   
    

        while True:
            option = input("Choose an option (1 for sending a message, 2 for playing a video, 3 for Quit): \n")

            if option == '1':
                keys_list = list(clients.keys())
                print(keys_list)
                recipient_name = input("Enter the recipient's name: ").strip()
                if recipient_name in clients:
                    try:
                        message = input("Enter the message you want to send: ")
                        client_message = name + ": " + message
                        recipient_public_key = clients[recipient_name]
                        secure_communication(client_socket, client_message, recipient_public_key)
                    except ValueError as e:
                       print("Error:", e)  # Print the ValueError message
                    except Exception as ex:
                       print("An unexpected error occurred:", ex, "might have left the server.")
                else:
                    print("Recipient not found in the directory.")
                    
                
            elif option == '2':
                client_socket.send("List Available Videos".encode())
                time.sleep(1)

                # Request to play a video
                video_name = input("Enter the name of the video you want to play (print only video name no need of other part i.e. _240p.mp4 is not needed): ")
                if video_name+"_240p.mp4" not in video_list or video_name+"_720p.mp4" not in video_list or video_name+"_1440p.mp4" not in video_list:
                    print("Video does not exist or video's all 3 resolution's are not in server directory.")
                else:
                    print("Requesting video")
                    client_socket.send(f"Play {video_name}".encode())

                
            elif option == '3':
                client_socket.send("QUIT".encode())
                break
                
            else:
                print("Invalid option. Please choose again.")
                
        main_thread.join()


if __name__ == "__main__":
    main()
