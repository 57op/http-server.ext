import json

class Response:
	def __init__(self, data, content_type, encoding='utf-8', headers={}):
		if isinstance(data, str):
			data = data.encode(encoding)

		headers['Content-Type'] = f'{content_type}; charset={encoding}'
		headers['Content-Length'] = len(data)

		self.data = data
		self.headers = headers

class JsonResponse(Response):
	def __init__(self, data, encoding='utf-8', headers={}):
		super().__init__(json.dumps(data), 'application/json', encoding=encoding, headers=headers)

class FileResponse(Response):
	def __init__(self, file, content_type, encoding='utf-8', headers={}):
		with open(file, 'rb') as fh:
			page = fh.read()

		super().__init__(page, content_type, encoding=encoding, headers=headers)