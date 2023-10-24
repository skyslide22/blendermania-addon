import json
import os
import sys
from typing import List
import bpy
import socketserver
import http.server
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

import subprocess

import mathutils

from .ServerActions import EditorTrail, focus_blender, process_editor_trails
from ..operators.OT_Items_Export import close_convert_panel
from .Functions import in_new_thread



class MyHandler(SimpleHTTPRequestHandler):

    def do_POST(self):
        success = False

        # if self.path == "/update_editortrails":
        if self.path == "/trails":
            content_len = int(self.headers.get('Content-Length'))
            post_body = self.rfile.read(content_len).decode().replace("}{", "},{")

            # with open("post_body.json", "w") as f:
            #     f.write(post_body)
            #     print(f"Wrote out to post_body.json. {os.curdir}")

            jsoncontent = json.loads(post_body)
            success = process_editor_trails(jsoncontent)

        else:
            print("no post data")

        r="""Access denied""" if not success else "Success"

        self.send_response(200 if success else 403)
        self.send_header("Content-type", "application/json;charset=utf-8")

        self.send_header("Content-length", len(r))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(r.encode("utf-8"))
        self.wfile.flush()


    def do_GET(self):

        success = False

        if self.path == "/focus_blender":
            success = focus_blender()


        r="""Access denied""" if not success else "Success"

        self.send_response(200 if success else 403)
        self.send_header("Content-type", "application/json;charset=utf-8")

        self.send_header("Content-length", len(r))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(r.encode("utf-8"))
        self.wfile.flush()

        # if focus_blender:
        #     print("blender focused, shut down server")
        #     raise KeyboardInterrupt()


@in_new_thread
def run_server() -> None:
    HandlerClass = MyHandler
    Protocol     = "HTTP/1.1"
    port         = 42069

    server_address = ('', port)

    HandlerClass.protocol_version = Protocol

    try:
        httpd = socketserver.TCPServer(server_address, HandlerClass)
        print(f"Server Started: {port}")
        httpd.serve_forever()

    except OSError as err:
        print("server already runs on" + str(port))

    except KeyboardInterrupt:
        print('Shutting down server')
        httpd.socket.close()
