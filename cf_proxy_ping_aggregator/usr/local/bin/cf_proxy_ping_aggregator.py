#!/usr/bin/env python3
import sys
import http.server
import socketserver
import argparse
import threading
import http.client
import time
from urllib.parse import urlparse

def output(line, isError):
    if isError:
        print(line, file=sys.stderr, flush=True)
    else:
        print(line, flush=True)


class ProxyHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Désactive le log automatique de BaseHTTPRequestHandler
        return

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request()

    def handle_request(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        start_time = time.time()
        responses = []
        has_error_response = False

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
            except Exception as e:
                has_error_response = True
                responses.append({
                    'port': port,
                    'status': 500,
                    'body': b'error',
                    'time': time.time() - start_time
                })

        # Sélectionne la réponse finale
        status_200_responses = [r for r in responses if r['status'] == 200 and r['body'].decode().strip() == 'pong']
        if status_200_responses:
            final_response = status_200_responses[0]
        else:
            fastest_response = min(responses, key=lambda r: r['time'])
            final_response = fastest_response

        # Détermine si la réponse finale est une erreur
        final_is_error = (final_response['status'] != 200 or final_response['body'].decode().strip() != 'pong')

        # Envoie la réponse
        self.send_response(final_response['status'])
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(final_response['body'])))
        self.end_headers()
        self.wfile.write(final_response['body'])

        # Log la requête principale
        output(
            f"{self.client_address[0]} - - [{self.log_date_time_string()}] \"{self.command} {self.path} {self.request_version}\" {final_response['status']} {len(final_response['body'])}",
            final_is_error
        )

        # Log les réponses individuelles
        for r in responses:
            output(
                f"  - Port {r['port']} → Status: {r['status']}, Body: {r['body'].decode()[:10]}.., Temps: {r['time']:.3f}s",
                r['status'] != 200 or r['body'].decode().strip() != 'pong'
            )

parser = argparse.ArgumentParser(description='Local HTTP Proxy Aggregator')
parser.add_argument('--port', type=int, required=True, help='Port to listen on')
parser.add_argument('--lport', type=int, action='append', required=True, help='Local ports to forward requests to')
args = parser.parse_args()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, local_ports):
        super().__init__(server_address, RequestHandlerClass)
        self.local_ports = local_ports

server = ThreadedHTTPServer(('', args.port), ProxyHTTPRequestHandler, args.lport)
output(f"Listening on port {args.port}, forwarding to ports {args.lport}", False)
server.serve_forever()
