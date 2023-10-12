#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body
    
    def __repr__(self) -> str:
        return f"Code: {self.code}\r\nBody: {self.body}"

class HTTPClient(object):
    def get_host_port(self,url):
        PORT_BY_SCHEME = {
        "http": 80,
        "https": 443,
        }
        parsed_url = urllib.parse.urlparse(url)
        port = parsed_url.port if parsed_url.port else PORT_BY_SCHEME[parsed_url.scheme] # get port by schema
        path = '/' if len(parsed_url.path) == 0 else parsed_url.path # default path '/' if no path is provided
        return parsed_url.hostname, port, path

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        status_line = data.split("\r\n")[0] # first line is status_line
        return int(status_line.split(' ')[1])

    def get_headers(self,data):
        headers = {}
        lines = data.split("\r\n")
        lines.pop(0) # remove status line
        for line in lines:
            if len(line.strip()) == 0: # empty line indicates start of body
                return headers
            header = line.strip().split(':', 1)
            headers[header[0].strip()] = header[1].strip()
        raise SyntaxError # should never reach here

    def get_body(self, data):
        return re.search(f"\r\n\r\n(.*)", data, re.S).group(1) # body is after \r\n\r\n
    
    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        hostname, port, path = self.get_host_port(url)
        self.connect(hostname, port)
        self.sendall(f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n")
        response = self.recvall(self.socket)
        self.close()
        # parse response
        code = self.get_code(response)
        headers = self.get_headers(response)       
        body = self.get_body(response)
        
        print("Headers:", headers)
        
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        hostname, port, path = self.get_host_port(url)
        payload = urllib.parse.urlencode(args) if args is not None else '' # encode args
        self.connect(hostname, port)
        self.sendall(f"POST {path} HTTP/1.1\r\nHost: {hostname}\r\nContent-Type: application/json\r\nContent-Length: {len(payload.encode('utf-8'))}\r\nConnection: close\r\n\r\n{payload}")
        response = self.recvall(self.socket)
        self.socket.close()
        # parse response
        code = self.get_code(response)
        headers = self.get_headers(response)       
        body = self.get_body(response)
        
        print("Headers:", headers)
        
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
