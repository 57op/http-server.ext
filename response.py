import json

class Response:
	def __init__(self, data, content_type, encoding='utf-8', headers=None):
		if isinstance(data, str):
			data = data.encode(encoding)

		self.data = data

		self.headers = {}
		self.headers['Content-Type'] = f'{content_type}; charset={encoding}'
		self.headers['Content-Length'] = len(self.data)

		if isinstance(headers, dict):
			for k, v in headers.items():
				self.headers[k] = v

class JsonResponse(Response):
	def __init__(self, data, encoding='utf-8', headers=None):
		super().__init__(json.dumps(data), 'application/json', encoding=encoding, headers=headers)

class FileResponse(Response):
	def __init__(self, file, content_type, encoding='utf-8', headers=None):
		with open(file, 'rb') as fh:
			page = fh.read()

		super().__init__(page, content_type, encoding=encoding, headers=headers)