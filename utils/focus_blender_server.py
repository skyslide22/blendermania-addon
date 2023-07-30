import sys

import http.server
from http.server import HTTPServer
from http.server import SimpleHTTPRequestHandler

import subprocess

from .Functions import in_new_thread

class MyHandler(SimpleHTTPRequestHandler):

    assets_path: str = ""

    def __init__(self,req,client_addr,server):
        SimpleHTTPRequestHandler.__init__(self,req,client_addr,server)      

    def do_GET(self):
        
        focus_blender = self.path == "/focus_blender"

        if(focus_blender):
            subprocess.Popen([
                MyHandler.assets_path + "/convert_report/focus_blender.bat",
                "blender"
            ])

        r="""Access denied""" if focus_blender else "blender focused"
        
        self.send_response(200 if focus_blender else 403)
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
def run_server(assets_path: str) -> None:

    HandlerClass = MyHandler
    HandlerClass.assets_path = assets_path
    Protocol     = "HTTP/1.1"
    port = 42069

    server_address = ('localhost', port)

    HandlerClass.protocol_version = Protocol

    try:
        httpd = HTTPServer(server_address, MyHandler)
        print ("Server Started")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Shutting down server')
        httpd.socket.close()