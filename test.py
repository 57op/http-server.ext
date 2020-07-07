import sys
import re

from app import App
from response import Response, JsonResponse, FileResponse

import unittest
import httpx
import json
import random

app = App(
	host='127.0.0.1',
	port=9999)

# define some routes
@app.error(code='[45][0-9]{2}')
def not_found(code, **args):
  return f'{code}', code

@app.route(path='/', methods=['GET'])
def root():
	return Response('root', 'text/plain')

@app.route(path='/', methods=['POST'])
def root():
	return Response('post root', 'text/plain')

@app.route(path='/json', methods=['POST'], accepts=['json'])
def json_cat(json):
  return JsonResponse(json)

@app.route(path='/form', methods=['POST'], accepts=['form'])
def form_cat(form):
  return JsonResponse(form)

@app.route(path='/qs', methods=['GET'], accepts=['querystring'])
def qs_cat(querystring):
  return JsonResponse(querystring)

@app.route(path='/path/(?P<str_a>[a-z]+)(?:/(?P<int_b>[0-9]+))?', methods=['GET'])
def path_cat(a, b):
  r = { 'a': a }

  if b is not None:
    r['b'] = b

  return JsonResponse(r)

@app.route(path='/case_does_not_matter', methods=['GET'], flags=re.I)
def cis():
  return 'it does not'

@app.route(path='/code/(?P<int_code>20[0-9]|226|232|26[259])', methods=['GET'])
def code_cat(code):
  print(code)
  return '', code

# and test later with an http client
url = f'http://{app.config["host"]}:{app.config["port"]}'

class TestApp(unittest.TestCase):
  def test_root(self):
    res = httpx.get(f'{url}/')
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.read().decode(), 'root')

    res = httpx.post(f'{url}/')
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.read().decode(), 'post root')

  def test_json_cat(self):
    json_in = {
      'test': 'okay',
      'list': [1,2,3],
      'bool': True,
      'nest': {
        'nested': ['well!'],
        'rand': random.random()
      }
    }
    res = httpx.post(f'{url}/json', json=json_in)
    self.assertEqual(res.status_code, 200)

    json_out = res.json()
    self.assertEqual(json.dumps(json_in, sort_keys=True), json.dumps(json_out, sort_keys=True))

  def test_form_cat(self):
    json_in = {
      'test': 'okay',
      'list': [1,2,3],
      'rand': 0.6541747266016014
    }
    res = httpx.post(f'{url}/form', data=json_in)
    self.assertEqual(res.status_code, 200)

    json_out = res.json()
    self.assertEqual(
      '{"list": ["1", "2", "3"], "rand": ["0.6541747266016014"], "test": ["okay"]}',
      json.dumps(json_out, sort_keys=True))

  def test_qs_cat(self):
    json_in = {
      'test': 'okay',
      'list': [1,2,3],
      'rand': 0.6541747266016014
    }
    res = httpx.get(f'{url}/qs', params=json_in)
    self.assertEqual(res.status_code, 200)

    json_out = res.json()
    self.assertEqual(
      '{"list": ["1", "2", "3"], "rand": ["0.6541747266016014"], "test": ["okay"]}',
      json.dumps(json_out, sort_keys=True))

  def test_path_cat(self):
    res = httpx.get(f'{url}/path/ciao1/53')
    self.assertEqual(res.status_code, 404)

    res = httpx.get(f'{url}/path/ciao')
    self.assertEqual(res.status_code, 200)
    j = res.json()
    self.assertEqual(j['a'], 'ciao')
    self.assertTrue(j.get('b') is None)

    res = httpx.get(f'{url}/path/ciao/53')
    self.assertEqual(res.status_code, 200)
    j = res.json()

    self.assertEqual(j['a'], 'ciao')
    self.assertEqual(j['b'], 53)

    res = httpx.get(f'{url}/path/ciao/53.5')
    self.assertEqual(res.status_code, 404)

  def test_char_case(self):
    def case_perm(s):
      sU = ''

      for c in s:
        if random.randint(0, 1) == 1:
          sU += c.upper()
        else:
          sU += c

      return sU

    for _ in range(10):
      res = httpx.get(f'{url}/{case_perm("case_does_not_matter")}')
      self.assertEqual(res.status_code, 200)

  def test_code(self):
    # check some codes
    codes = [200,201,202,203,204,205,206,207,208,209,226,232,262,265,269]

    for code in codes:
      res = httpx.get(f'{url}/code/{code}')
      self.assertEqual(res.status_code, code)

def http_thread(app):
  print(f'Serving on http://{app.config["host"]}:{app.config["port"]}')
  app.run()

def test_thread(app):
  suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestApp)
  runner = unittest.TextTestRunner()
  runner.run(suite)

if __name__ == '__main__':
  from threading import Thread

  Thread(target=http_thread, args=(app,)).start()
  Thread(target=test_thread, args=(app,)).start()