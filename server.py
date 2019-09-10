#!/usr/bin/env python3
import zmq

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5556")

while True:
    data = input(">>> ")
    socket.send_string(data)
