import gradio as gr
import modules.shared as shared

import json

import os
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, quote

import mimetypes
import time
import socket

def format_date(time_value):
    # Format the provided time_value as a date string
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(time_value))


from modules import chat

right_symbol = '\U000027A1'
left_symbol = '\U00002B05'
refresh_symbol = '\U0001f504'  # 🔄

paragraphs = []

current_prev = 0
file_namePARAMJSON = "massrewriter.json"
jsonfile = []
plaintextfile = ''
file_nameJSON = "output.json"
file_nameTXT = "output.txt"

params = {
        "display_name": "File Server",
        "is_tab": True,
}

class FileLister(SimpleHTTPRequestHandler):
    directory = "."  # Default root directory
    def send_file(self, path, as_attachment=False, download_name=None):
        try:
            if not os.path.exists(path) or not os.path.isfile(path):
                self.send_response(404)
                self.end_headers()
                return

            if download_name is None:
                download_name = os.path.basename(path)

            content_type, encoding = mimetypes.guess_type(download_name)
            if content_type is None:
                content_type = "application/octet-stream"

            if as_attachment:
                disposition = f'attachment; filename="{quote(download_name)}"'
            else:
                disposition = f'inline; filename="{quote(download_name)}"'

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", disposition)
            self.send_header("Content-Length", str(os.path.getsize(path)))
            self.send_header("Last-Modified", format_date(os.path.getmtime(path)))
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")

            with open(path, "rb") as file:
                self.end_headers()
                self.wfile.write(file.read())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode("utf-8"))
    def list_files(self, directory):
        try:
            files = os.listdir(directory)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()

            # Create a title with the current directory path
            title = f"<h2>Directory: {directory}</h2>"

            # Create a bullet list for the links
            list_items = ""

            # Add a special link to navigate up one directory level
            parent_directory = os.path.dirname(directory)
            #if directory != parent_directory:
            #    parent_url = f"/list_files?directory={quote(parent_directory)}"
            #    list_items += f'<li><a href="{parent_url}">[..]</a></li>'

            for file_name in files:
                file_path = os.path.join(directory, file_name)
                if os.path.isdir(file_path):
                    # If it's a directory, create a link to list its contents
                    file_url = f"/list_files?directory={quote(file_path)}"
                    list_items += f'<li><a href="{file_url}">{file_name}/</a></li>'
                else:
                    # If it's a file, create a link to download it
                    relative_path = os.path.relpath(file_path, start=self.directory).replace("\\", "/")
                    list_items += f'<li><a href="{quote(relative_path)}">{file_name}</a></li>'

            # Create the HTML content with the title and bullet list
            html = f"<html><head>{title}</head><body><ul>{list_items}</ul></body></html>"

            self.wfile.write(html.encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode("utf-8"))

    def do_GET(self):
        if self.path.startswith("/list_files"):
            directory_param = unquote(self.path.split("?directory=")[-1]) if "?" in self.path else ""
            directory = os.path.abspath(directory_param) if directory_param else os.getcwd()

            if not os.path.exists(directory) or not os.path.isdir(directory):
                self.send_error(404, "Directory not found")
                return

            self.list_files(directory)
        else:
            super().do_GET()


def start_server(port=8080, directory="."):
    server_address = ("", port)
    global httpd
    httpd = HTTPServer(server_address, FileLister)
    FileLister.directory = os.path.abspath(directory)  # Set the root directory

      # Get the local IP address of the server
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)


    print(f"File Server is running on http://{ip_address}:{port}")


    httpd.serve_forever()

    yield f"File Server is running on http://{ip_address}:{port}"

def stop_server():
    if hasattr(globals(), 'httpd'):
        print("Stopping the server...")
        yield f"Stopping...."
        httpd.shutdown()
        print("Server stopped.")
        yield f"Server stopped."
    else:
        print("Server is not running.")
        yield f"Server is not running."


def ui():
    global params

    with gr.Row():
        with gr.Column():
            with gr.Row():
                start_btn = gr.Button('Start File Server', variant='primary')
                cancel_btn = gr.Button('Stop File Server',variant='stop')
            with gr.Row():
                infotext2 = gr.Markdown(value='Ready')

    start_btn.click(start_server,None,infotext2)

    cancel_btn.click(stop_server,None,infotext2)

