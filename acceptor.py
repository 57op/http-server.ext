import json
import urllib.parse

class HTTPArgumentAcceptor:
	def __init__(self, app):
		pass

	def args(self):
		pass

class QueryStringArgumentAcceptor(HTTPArgumentAcceptor):
	def __init__(self, app):
		self._args = urllib.parse.parse_qs(app.querystring, keep_blank_values=True)

	def args(self):
		return self._args

class BodyArgumentAcceptor(HTTPArgumentAcceptor):
	def __init__(self, app):
		assert app.command in ('POST', 'PUT'), f'{app.command} is not a valid method for BodyArgumentAcceptor'

		content_type = app.headers.get('Content-Type')
		assert content_type is not None, 'header Content-Type is not defined, cannot proceed'

		encoding = app.config['default_encoding']

		try:
			content_type, encoding = content_type.split(';', maxsplit=1)
			encoding = encoding.strip()[len('charset='):]
		except ValueError:
			pass

		content_length = int(app.headers.get('Content-Length', -1))
		data = app.rfile.read(content_length).decode(encoding)

		self.content_type = content_type
		self.data = data

class FormArgumentAcceptor(BodyArgumentAcceptor):
	def __init__(self, app):
		super().__init__(app)

	def args(self):
		return urllib.parse.parse_qs(self.data, keep_blank_values=True) \
			if self.content_type == 'application/x-www-form-urlencoded' else None

class JsonArgumentAcceptor(BodyArgumentAcceptor):
	def __init__(self, app):
		super().__init__(app)

	def args(self):
		return json.loads(self.data) if self.content_type == 'application/json' else None