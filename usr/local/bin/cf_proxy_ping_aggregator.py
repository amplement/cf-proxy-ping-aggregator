#!/usr/bin/env python3

import http.server
import socketserver
import argparse
import threading
import http.client
import time
from urllib.parse import urlparse

def output(line, logPath):
    if logPath:
        with open(logPath, 'a') as f:
            f.write(line + '\n')
    else:
        print(line)

class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        start_time = time.time()

        responses = []
        for port in self.server.local_ports:
            try:
                conn = http.client.HTTPConnection('localhost', port, timeout=5)
                conn.request(self.command, self.path, body, dict(self.headers))
                response = conn.getresponse()
                response_body = response.read()
                elapsed = time.time() - start_time
                responses.append({
                    'port': port,
                    'status': response.status,
                    'body': response_body,
                    'time': elapsed
                })
                conn.close()
            except Exception:
                responses.append({
                    'port': port,
                    'status': 500,
                    'body': b'error',
                    'time': time.time() - start_time
                })

        status_200_responses = [r for r in responses if r['status'] == 200 and r['body'] == b'pong']
        if status_200_responses:
            final_response = status_200_responses[0]
        else:
            fastest_response = min(responses, key=lambda r: r['time'])
            final_response = fastest_response

        self.send_response(final_response['status'])
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(final_response['body'])))
        self.end_headers()
        self.wfile.write(final_response['body'])
        logPath = hasattr(server, 'logfile') and server.logfile
        output(f"{self.client_address[0]} - - [{self.log_date_time_string()}] \"{self.command} {self.path} {self.request_version}\" {final_response['status']} {len(final_response['body'])}", logPath)
        
        for r in responses:
            output(f"  - Port {r['port']} → Status: {r['status']}, Body: {r['body'].decode()}, Temps: {r['time']:.3f}s", logPath)

parser = argparse.ArgumentParser(description='Local HTTP Proxy Aggregator')
parser.add_argument('--port', type=int, required=True, help='Port to listen on')
parser.add_argument('--lport', type=int, action='append', required=True, help='Local ports to forward requests to')
parser.add_argument('--logfile', type=str, help='Chemin du fichier de log (optionnel)')
args = parser.parse_args()

logPath = getattr(args, 'logfile', None)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, local_ports):
        super().__init__(server_address, RequestHandlerClass)
        self.local_ports = local_ports
        self.logfile = logPath

server = ThreadedHTTPServer(('', args.port), ProxyHTTPRequestHandler, args.lport)
output(f"Listening on port {args.port}, forwarding to ports {args.lport}", logPath)

server.serve_forever()
