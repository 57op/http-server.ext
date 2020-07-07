import re

from pydoc import locate

class Route:
	def __init__(self, rpath, accepts, handler, rflags=0):
		self.rpath = re.compile(f'^{rpath}$', flags=rflags)
		self.accepts = accepts
		self.handler = handler

	def matches(self, path):
		vars = None

		if m := self.rpath.match(path):
			vars = Route.cast_dict(m.groupdict())

		return vars

	@staticmethod
	def cast_dict(pathvars):
		vars = {}

		for key, value in pathvars.items():
			try:
				type_cast, key = key.split('_', maxsplit=1)
				type_cast = locate(type_cast) or str
			except ValueError:
				type_cast = str

			vars[key] = None if value is None else type_cast(value)

		return vars

class ErrorRoute:
	def __init__(self, rcode, handler, rflags=0):
		self.rcode = re.compile(f'^{rcode}$', flags=rflags)
		self.handler = handler

	def matches(self, code):
		if type(code) == int:
			code = str(code)

		vars = None

		if m := self.rcode.match(code):
			vars = { 'code':  int(m.group(0)) }

		return vars