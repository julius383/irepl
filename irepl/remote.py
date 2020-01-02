#!/usr/bin/env python3
import os
import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.SUB)

socket.connect("tcp://localhost:5556")
socket.setsockopt_string(zmq.SUBSCRIBE, "")
data = socket.recv_string()
while data:
    print("{0} = {1}".format(data, eval(data)))
    data = socket.recv_string()
