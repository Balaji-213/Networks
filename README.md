# Video Link:
https://drive.google.com/file/d/1CyCCUok3mcmu1IVmDvxdh3n9qjn-YNDV/view?usp=sharing


# Secure Video Streaming Application:
This Python application enables secure communication and real-time video streaming between clients and a server. 

## Features:
`Secure Communication`: Utilizes RSA encryption to ensure secure messaging between clients and the server.
`Client Directory`: Maintains a directory of connected clients and their public keys for secure communication.
`Video Streaming`: Streams video files to clients upon request, supporting multiple resolutions.
`Error Handling`: Implements error handling for various network and connection-related issues.
`Concurrent Processing`: Utilizes multithreading to handle multiple client connections simultaneously.

## Requirements:
```bash
Python 3.x
OpenCV (cv2)
imutils
PyCryptoDome (Crypto)
json
socket
threading
os
struct
pickle
queue
time
```

## Code Files:

### 210010008_server.py
The `210010008_server.py` script serves as the server component of the application. It handles client connections, message processing, and video streaming. Key features include:

1. `Secure Communication`: Utilizes RSA encryption for secure messaging between clients and the server.
2. `Client Directory`: Maintains a directory of connected clients and their public keys for secure communication.
3. `Video Streaming`: Streams video files to clients upon request, supporting multiple resolutions.
4. `Multithreading`: Utilizes multithreading to handle multiple client connections simultaneously.

### 210010008_client.py
The `210010008_client.py` script represents the client component of the application. It allows users to connect to the server, send messages, request to play videos, and disconnect from the server. Key features include:

1. `Connection Establishment`: Clients establish connections with the server by providing a unique name and their RSA public key.
2. `Message Encryption`: Messages sent by clients are encrypted using RSA encryption for secure communication.
3. `Video Playback`: Clients can request to play available videos from the server, which are streamed in real-time.


## Program Structure:

The program follows a client-server architecture, where the server handles incoming client connections, maintains a directory of connected clients, and manages video streaming. The server script (210010008_server.py) consists of functions to handle client connections, message processing, and video streaming.

The client script (210010008_client.py) allows users to connect to the server, send messages, request to play videos, and disconnect from the server. It includes functions for establishing connections, encrypting messages, and processing video playback requests.

## RUN Format:
Keep all the code and video in same directory.
Open termainal in that directory and then run followig commands:
1. To run server
```bash
python 210010008_server.py
```
2. To run client
```bash
python 210010008_client.py
```

### NOte:
    Make sure you create `videos/` directory and store all the video in that file as my code requires it in such format.
    Make sure to keep all the three videos of format <video-name>_240p.mp4 , <video-name>_720p.mp4 and <video-name>_1440p.mp4 are in the videos/diretory.


## Demo Instructions:

1.  `Server Setup`:
    Run the `210010008_server.py` script on a server machine.
    Ensure that the server is listening on the specified host and port. Specifically `localhost` and `9999` in my code.

2.  `Client Connections`:
    Run the `210010008_client.py` script on client machines.
    Provide a unique name and RSA public key will be generated for each client.
    Connect to the server using the provided host and port.

3. `Messaging`:
    Clients can send encrypted messages to other connected clients.
    Messages are decrypted by the server and forwarded to the intended recipients.

4. `Video Streaming`:
    Clients can request to play available videos from the server.
    Videos are streamed in real-time at different resolutions (240p, 720p, 1440p) one after the other.

5.  `Disconnecting`:
    Clients can gracefully disconnect from the server by sending a `"QUIT"` message.
    The server updates the client directory and broadcasts the updated information to all connected clients.

## Error-Handling:

1.  Server will not accept 2 clients with same username, the second user who is trying to connect will receive an error message indicating this and will be disconnected.
2. Implemented to locks in server to make sure no data is being worngly read or written in Queues.
3. Receiveing size will automatically be calculated and handled in the clients side, receving data in chunks.
4. Client can PLAY video and still can receive  text messages if it's playing any video at the backend, message will be diplayed after video transmission is done.
5. Can play multiple video at the same time.
6. New client can connect while previous client is Playing video.
7. The message encryption limited to 2048 bits. If user tries to send more than that it will raise an exception.
8. Used Queuing to make sure no data is being missed out while processing.
9. If any one of the resolutions is not present the video will not play. It will raise an error.