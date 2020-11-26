#!/usr/bin/python3

import random
import time
from socketserver import ThreadingMixIn
import xmlrpc
from xmlrpc.server import SimpleXMLRPCServer,SimpleXMLRPCDispatcher,SimpleXMLRPCRequestHandler
import ssl
import sys
import traceback

import locale
locale.setlocale(locale.LC_ALL, 'C.UTF-8')

import n4d.server.core

DEBUG=True

def dprint(data):
	if DEBUG:
		print("[Server] %s"%data)

class N4dServer:
	
	N4D_KEYFILE='/etc/n4d/cert/n4dkey.pem'
	N4D_CERTFILE='/etc/n4d/cert/n4dcert.pem'
	SECURE_SERVER=True

	class N4dCallHandler(SimpleXMLRPCRequestHandler):
		
		def do_POST(self):
			#Copied from libpython3.6-stdlib:amd64: /usr/lib/python3.6/xmlrpc/server.py
			
			if not self.is_rpc_path_valid():
				self.report_404()
				return

			try:

				max_chunk_size = 10*1024*1024
				size_remaining = int(self.headers["content-length"])
				L = []
				while size_remaining:
					chunk_size = min(size_remaining, max_chunk_size)
					chunk = self.rfile.read(chunk_size)
					if not chunk:
						break
					L.append(chunk)
					size_remaining -= len(L[-1])
				data = b''.join(L)

				data = self.decode_request_content(data)
				if data is None:
					return #response has been sent

				# MODIFIED HERE TO INCLUDE N4D EXTRA INFO TO MODIFY CALL ARGS IF NECESARY
				n4d_extra={}
				addr,pid=self.client_address
				n4d_extra["client_address"]=addr
				n4d_extra["client_pid"]=pid
				response = self.server._marshaled_dispatch(data, getattr(self, '_dispatch', None), self.path,n4d_extra)

			except Exception as e: 
				print(e)
				self.send_response(500)

				if hasattr(self.server, '_send_traceback_header') and self.server._send_traceback_header:
					self.send_header("X-exception", str(e))
					trace = traceback.format_exc()
					trace = str(trace.encode('ASCII', 'backslashreplace'), 'ASCII')
					self.send_header("X-traceback", trace)

					self.send_header("Content-length", "0")
					self.end_headers()
			else:
				
				self.send_response(200)
				self.send_header("Content-type", "text/xml")
				if self.encode_threshold is not None:
					if len(response) > self.encode_threshold:
						q = self.accept_encodings().get("gzip", 0)
						if q:
							try:
								response = gzip_encode(response)
								self.send_header("Content-Encoding", "gzip")
							except NotImplementedError:
								pass
				self.send_header("Content-length", str(len(response)))
				self.end_headers()
				self.wfile.write(response)

	class ThreadedXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
		
		def process_request_thread(self,request,client_address):

			ThreadingMixIn.process_request_thread(self,request,client_address)
		
		def _marshaled_dispatch(self, data, dispatch_method = None, path = None, n4d_extra_info=None):

			self.allow_none=True
			try:

				params, method = xmlrpc.client.loads(data)
				params=(n4d_extra_info,)+params

				if dispatch_method is not None:
					response = dispatch_method(method, params)
				else:

					response = self._dispatch(method, params)

				response = (response,)
				response = xmlrpc.client.dumps(response, methodresponse=1,allow_none=self.allow_none, encoding=self.encoding)

			except xmlrpc.client.Fault as fault:
				dprint("Captured xmlrpc.client.Fault exception: %s\n"%fault)
				response = xmlrpc.client.dumps(fault, allow_none=self.allow_none,encoding=self.encoding)
			except Exception as e:
				dprint("Captured unhandled exception: %s"%e)
				exc_type, exc_value, exc_tb = sys.exc_info()
				traceback_str=traceback.format_exc()
				dprint(traceback_str)
				response = xmlrpc.client.dumps(xmlrpc.client.Fault(1, "Captured unhandled exception: %s" % (traceback_str)),encoding=self.encoding, allow_none=self.allow_none,)

			response=bytearray(response,self.encoding)
			return response	

	def init_server(self,host,port):
		
		dprint("Starting N4D ...")
		self.core=n4d.server.core.Core.get_core(DEBUG)
		self.server_host=host
		self.server_port=port
		self.handler=N4dServer.N4dCallHandler
		self.handler.encode_threshold=None
		self.server=N4dServer.ThreadedXMLRPCServer((host,port),self.handler,DEBUG)
		#allow_none
		SimpleXMLRPCDispatcher.__init__(self.server,allow_none=True)
		
		self.wrap_ssl()
		self.server.register_instance(self.core)
		
	#def init_server
	
	def wrap_ssl(self):
		
		if N4dServer.SECURE_SERVER:
			self.server.socket=ssl.wrap_socket(self.server.socket,N4dServer.N4D_KEYFILE,N4dServer.N4D_CERTFILE)
			
	#def wrap_ssl
	
	
	def start_server(self):
		
		dprint("N4D server ready at port %s (Press CTRL+c to exit) ...\n"%(self.server_port))

		try:
			self.server.serve_forever()
		except KeyboardInterrupt:
			dprint("")
			dprint("[SERVER] Exiting...")
			return
		
	#def start_server


if __name__ == '__main__':
	n=N4dServer()
	n.init_server("",9800)
	n.start_server()