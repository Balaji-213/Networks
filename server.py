import socket
import threading
import os
import json
import cv2
import imutils
import pickle
import struct
from queue import Queue
import time
    
QUEUE_SIZE = 15   

# Dictionary to store clients' information
clients = {}
clients_sockets = {}

# Dictionary to map client sockets to message queues
client_queues = {}

# Define the directory where video files are stored
VIDEO_DIRECTORY = "videos/"
FRAME_RATE = 30

lock = threading.Lock()

def queue_messages(client_socket, socket_address, name):
    # Create a message queue for the client if it doesn't exist
    with lock:
        client_queues[socket_address] = Queue(maxsize=QUEUE_SIZE)

    while True:
        try:
            # Receive message from client
            data = client_socket.recv(1024)
            if not data:
                break

            # Enqueue the message in the client's queue
            with lock:
                client_queues[socket_address].put(data)
                print("Message from Client")

        except ConnectionAbortedError:
            # Handle the case when the connection is abruptly terminated
            print(f"Connection with client {socket_address} was terminated")
            break
        
        except ConnectionResetError:
            with lock:
                del clients[name]
                del clients_sockets[name]
                del client_queues[socket_address] 
            broadcast_clients_info()   
            print(f"Connection with client {socket_address} was forcefully terminated")
            break

        except Exception:
            break
    exit(0)


def handle_client(client_socket, client_address, name):
    while True:
        try:
            client_queue = client_queues[client_address]
                # Process messages from the queue
            while not client_queue.empty():
                data = client_queue.get()
                # print("Data accessed")
                
                if not data:
                    print(f"Client {client_address} disconnected")
                    del clients[client_address]
                    broadcast_clients_info()
                    client_socket.close()
                    break

                decoded_data = data.decode()  # Decode the data

                # Handle data received from client
                if decoded_data.startswith("QUIT"):
                    with lock:
                        final_info = {
                            "Encrypted": False,
                            "Type": "QUIT"
                        }
                        json_string = json.dumps(final_info).encode()
                        json_size = len(json_string)
                        size_packed = struct.pack("Q", json_size)
                        client_socket.sendall(size_packed+json_string)
                        del clients[name]
                        del clients_sockets[name]
                        del client_queues[client_address]
                    broadcast_clients_info()
                    # print(clients)
                    client_socket.close()
                    break
                elif decoded_data.startswith("List Available Videos"):
                    videos = os.listdir(VIDEO_DIRECTORY)
                    videos = [video for video in videos if video.endswith(".mp4")]
                    json_data = {
                        "Encrypted": False,
                        "Type": "Videos List",
                        "Video": videos
                    }
                    json_string = json.dumps(json_data).encode()
                    json_size = len(json_string)
                    size_packed = struct.pack("Q", json_size)  
                    client_socket.sendall(size_packed+json_string)
                elif decoded_data.startswith("Play"):
                    # Extract video name from the client request
                    video_name = decoded_data.split()[1]
                    # Send acknowledgment
                    json_data = {
                        "Encrypted": False,
                        "Type": "Video Start",
                        "Message": f"Playing video {video_name} in different resolutions"
                    }
                    json_string = json.dumps(json_data).encode()
                    json_size = len(json_string)
                    size_packed = struct.pack("Q", json_size)  
                    client_socket.sendall(size_packed+json_string)
                    # client_socket.send(f"Playing video {video_name} in different resolutions".encode())
                    # Stream the video
                    play_video(client_socket, video_name)
                else:    
                    json_data = json.loads(decoded_data)
                    encoded_message = json_data["Encrypted"]
                    
                    json_size = len(data)
                    size_packed = struct.pack("Q", json_size)  

                    if (encoded_message):
                        for socket in clients_sockets.values():
                            try:
                                socket.sendall(size_packed+data)
                                print(f"Message forwarded to client {socket}")
                            except Exception as e:
                                print(f"Error forwarding message to client {socket}: {e}")
                                  
                           
        except KeyError:
            # Handle the case when the client socket is not found in the dictionary
            print(f"Message queue not found for client {client_address}")
            break
    exit(0)

        
def broadcast_clients_info():
    # Prepare data to broadcast
    broadcast_info = "Broadcast"
    clients_info_json = clients
    final_info = {
        "Encrypted": False,
        "Type": broadcast_info,
        "clients_info": clients_info_json
    }
    json_string = json.dumps(final_info).encode()
    json_size = len(json_string)
    size_packed = struct.pack("Q", json_size)  
    # Broadcast clients' information to all connected clients
    for client_socket in clients_sockets.values():
        try:
            client_socket.sendall(size_packed+json_string)
        except Exception as e:
            print(f"Error broadcasting new clients' info: {e}")


def play_video(conn, video_name):
    video_paths = [
        os.path.join(VIDEO_DIRECTORY, f"{video_name}_{res}p.mp4") for res in ["240", "720", "1440"]
    ]
    
    total_frames = None
    
    caps = [cv2.VideoCapture(path) for path in video_paths]
    for cap in caps:
        if not cap.isOpened():
            print(f"Error: Unable to open video file: {cap}")
            
    
    # Get total frames from the first video
    total_frames = int(caps[0].get(cv2.CAP_PROP_FRAME_COUNT))
    frame_size = total_frames // 3
    
    delay = 1 / FRAME_RATE
    
    for cap, start_frame in zip(caps, [0, frame_size, 2 * frame_size]):
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    for cap in caps:
        for _ in range(frame_size):
            ret, frame = cap.read()
            if not ret:
                break
            frame = imutils.resize(frame, width=720)
            a = pickle.dumps(frame)  
            message = struct.pack("Q", len(a)) + a
            conn.sendall(message)
            
            time.sleep(delay)

    # Send a message to indicate end of video
    conn.sendall(struct.pack("Q", len(b'done')) + b'done')
    
    # Release video captures
    for cap in caps:
        cap.release()
    

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 9999))
    server_socket.listen(5)
    print("Server is listening for connections...")

    while True:
        new_client = True
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")
        client_name = client_socket.recv(1024).decode()
        public_key_data = client_socket.recv(1024).decode()        
        # print(public_key_data)
        # print(public_key_string)    
        if client_name in clients:
            # Name is already in use, inform the client
            error_message = "Error: Name is already in use. Please choose a different name."
            client_socket.sendall(error_message.encode())
            new_client =False
            client_socket.close()  # Close the connection with the client
        else:
            # Name is not in use, store the name and public key data
            clients[client_name] = public_key_data
            clients_sockets[client_name] = client_socket
            success_message = f"Client {client_name} connected to the server successfully."
            client_socket.sendall(success_message.encode())
            time.sleep(0.001)
            
        if new_client:
            # Broadcast clients' information to all connected clients
            broadcast_clients_info()
            # Thread to handle each client separately
            receive_thread = threading.Thread(target=queue_messages, args=(client_socket,client_address, client_name))
            receive_thread.start()
            
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, client_name))
            client_thread.start()
            
if __name__ == "__main__":
    main()
