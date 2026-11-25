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

    def _respond(self, success: bool) -> None:
        # no Access-Control-Allow-Origin header: web pages must not be able to read the responses
        r = "Success" if success else "Access denied"
        body = r.encode("utf-8")
        self.send_response(200 if success else 403)
        self.send_header("Content-type", "application/json;charset=utf-8")
        self.send_header("Content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def do_POST(self):
        success = False

        if self.path == "/trails":
            try:
                content_len = int(self.headers.get('Content-Length') or 0)
                post_body = self.rfile.read(content_len).decode("utf-8").replace("}{", "},{")
                success = bool(process_editor_trails(json.loads(post_body)))
            except Exception as err:   # malformed requests must not raise in the server thread
                print(f"editor trails request rejected: {err}")
                success = False
        else:
            print("no post data")

        self._respond(success)


    def do_GET(self):
        success = False

        if self.path == "/focus_blender":
            try:
                success = focus_blender()
            except Exception as err:
                print(f"focus_blender failed: {err}")

        self._respond(success)

        # if focus_blender:
        #     print("blender focused, shut down server")
        #     raise KeyboardInterrupt()


@in_new_thread   # daemon thread: serve_forever() must not keep Blender alive on quit
def run_server() -> None:
    HandlerClass = MyHandler
    Protocol     = "HTTP/1.1"
    port         = 42069

    server_address = ('127.0.0.1', port)   # local only, never reachable from the network

    HandlerClass.protocol_version = Protocol

    try:
        httpd = socketserver.TCPServer(server_address, HandlerClass)
    except OSError:
        print("server already runs on " + str(port))
        return

    print(f"Server Started: {port}")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
