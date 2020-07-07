import http.server
import traceback

from types import MethodType

from response import Response
from route import Route, ErrorRoute
from acceptor import QueryStringArgumentAcceptor, FormArgumentAcceptor, JsonArgumentAcceptor

class App(http.server.BaseHTTPRequestHandler):
	ACCEPTORS = {
		'querystring': QueryStringArgumentAcceptor,
		'form': FormArgumentAcceptor,
		'json': JsonArgumentAcceptor
	}

	def __init__(self, **config):
		self.config = self._load_default_config(config)

		self.routes = {
			'DELETE': [],
			'HEAD': [],
			'GET': [],
			'OPTIONS': [],
			'POST': [],
			'PUT': []
		}
		self.errors = []
		self.acceptors = App.ACCEPTORS.copy()

		# dynamically define method handlers
		'''
		same as manually defining:
			def do_<METHOD>(self):
				self._do_any_catch('<METHOD>')
		'''
		for method in self.routes.keys():
			setattr(
				self,
				f'do_{method}',
				MethodType(lambda self: self._do_any_catch(), self))

	def __call__(self, request, client_address, server):
		# when HTTPServer calls the handler (passed as instantiated App object)
		# this will trigger the handling of the request: BaseHTTPRequestHandler
		super().__init__(request, client_address, server)
		return self

	# utilities methods, private

	def _load_default_config(self, config):
		config.setdefault('default_content_type', 'text/html')
		config.setdefault('default_encoding', 'utf-8')
		config.setdefault('host', '127.0.0.1')
		config.setdefault('port', '8080')

		return config

	def _get_route_handler(self, path, method):
		for route in self.routes[method]:
			if (pathvars := route.matches(path)) is not None:
				return route, pathvars

		# if nothing is found return 404
		return self._get_error_handler(404)

	def _get_error_handler(self, code):
		for err_route in self.errors:
			if (pathvars := err_route.matches(code)) is not None:
				return err_route, pathvars

		raise NotImplementedError('default error handler missing, please define one to catch and handle http errors')

	def _send_response(self, response):
		if isinstance(response, tuple):
			response, code = response
		else:
			code = 200

		if not isinstance(response, Response):
			response = Response(response, content_type=self.config['default_content_type'], encoding=self.config['default_encoding'])

		self.send_response(code)

		if not isinstance(response, Response):
			response = Response(response, content_type=self.config['default_content_type'], encoding=self.config['default_encoding'])

		for header, value in response.headers.items():
			self.send_header(header, value)

		self.end_headers()

		if self.command != 'HEAD':
			self.wfile.write(response.data)

	def _do_any(self):
		try:
			path, querystring = self.path.split('?', maxsplit=1)
		except ValueError:
			path = self.path
			querystring = None

		self.querystring = querystring

		# find the proper route handlers
		route, pathvars = self._get_route_handler(path, self.command)
		# accept allowed args (defined in App.acceptors)
		args_map = {}

		if isinstance(route, Route):
			for accept in route.accepts:
				acceptor = self.acceptors.get(accept)

				try:
					args_map[accept] = acceptor(self).args()
				except Exception as e:
					# return a bad request error
					route, pathvars = self._get_error_handler(400)
					pathvars['error'] = traceback.format_exc(-1)
					self._send_response(route.handler(**pathvars))
					return

		self._send_response(route.handler(**pathvars, **args_map))

	def _do_any_catch(self):
		try:
			self._do_any()
		except Exception as e:
			route, pathvars = self._get_error_handler(500)
			pathvars['error'] = traceback.format_exc(-1)
			self._send_response(route.handler(**pathvars))

			# report this exception, in a log file?
			raise e

	# function decorators for setting up routing

	def route(self, **decorator_kwargs):
		path = decorator_kwargs['path']
		methods = decorator_kwargs['methods']
		accepts = decorator_kwargs.get('accepts', [])
		flags = decorator_kwargs.get('flags', 0)

		for acceptor in filter(lambda acceptor: acceptor not in self.acceptors.keys(), accepts):
			raise AssertionError(f'invalid acceptor `{acceptor}`')

		def wrapper(handler):
			for method in methods:
				routes = self.routes.get(method)
				assert routes is not None, f'invalid method `{method}`'
				routes.append(Route(path, accepts, handler, rflags=flags))

		return wrapper

	def error(self, **decorator_kwargs):
		rcode = decorator_kwargs['code']

		def wrapper(handler):
			self.errors.append(ErrorRoute(rcode, handler))

		return wrapper

	# http server binding and running
	def run(self):
		with http.server.HTTPServer((self.config['host'], self.config['port']), self) as httpd:
			httpd.serve_forever()

	def add_acceptor(self, name, acceptor):
		self.acceptors[name] = acceptor

	def del_acceptor(self, name):
		del self.acceptors[name]