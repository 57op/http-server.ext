# http.server-ext
...is a routing extension for [python http.server](https://docs.python.org/3/library/http.server.html) module  
with other features such as url rewriting, querystring, form and json parsing.

## Usage
### Basics - Hello, World!
Create an `App` object:

```python
from app import App

app = App(
  default_content_type='text/html',
  default_encoding='utf-8',
  host='127.0.0.1',
  port=8080)
```

then define some routes:

```python
@app.route(path='/', methods=['GET'])
def app_hw():
  return 'Hello, World!', 200
```

When defining a route, the keyword arguments `path` and `methods` are required. No default method is implied.


The return value of a route handler (`app_hw` function in this case) can be a tuple consisting of  
`(response: Response or str, status_code: int).`  
Response object is explained later on this page.  
When status code is not specified, 200 is automatically assumed.

Then, start the http server:

```python
print(f'Serving on http://{app.config["host"]}:{app.config["port"]}')
app.run()
```

this will start the server and accepts/handles new requests until you manually exit.

### Regex paths
Now that the basics have been explained, let's move on some more interesting routing usages.  
For a route, the `path` keyword argument is actually compiled into a python regex.  

```python
@app.route(path='/user/(?P<str_name>\w+)', methods=['GET'])
def app_user(name):
  return f'Hello, {name}'
```

matched groups with a symbolic name attached will be passed to the handler function in their writing order.  
More over you can prefix the symbolic name with `type_` for type casting.  
This will work for native python types such as str, int, float. Anything else is undefined behaviour.  
Type prefix is not mandatory and the argument passed to the handler will simply be a string you can cast with a custom defined logic in the handler.

Let's do a final example:

```python
@app.route(path='/user/(?P<int_uid>[0-9]{1,5})(?:/(?P<name>\w+))?', methods=['GET'])
def app_user(uid, name):
  assert type(uid) == int
  assert type(name) == str or name is None
  return f'Hello, #{uid} {"No name" if name is None else name}'
```

We defined two groups: `uid` and `name`.  
`uid` is casted to an int type, `name` doesn't go through casting and therefore is a str type.  
Moreover, `name` group is optional and might be undefined (None).

### Querystring
In order for a route handler to get access to parsed query string data,  
it must be explicitly set in the definition step of the route:

```python
import json

@app.route(path='/qs', methods=['GET'], accepts=['querystring'])
def app_qs(querystring):
  return json.dumps(querystring)
```

So, suppose we do a GET request to this endpoint:

```
GET /qs?a=b&c=d&a=c
```

the result will be:

```
{"a": ["b", "c"], "c": ["d"]}
```

### Form data
In order for a route handler to get access to parsed form data,  
it must be explicitly set in the definition step of the route:

```python
import json

@app.route(path='/form', methods=['GET', 'POST', 'PUT'], accepts=['querystring', 'form'])
def app_form(querystring, form):
  if app.command == 'GET':
    assert form is None
    data = querystring
  else:
    assert form is not None
    data = form

  return json.dumps(data)
```

So, suppose we do a sequence of GET, POST and PUT requests to this endpoint:

```
GET /form?a=b&c=d&a=c

POST /form
a=b&c=d&a=c

PUT /form
a=b&c=d&a=c
```

the results will be:

```
{"a": ["b", "c"], "c": ["d"]}

{"a": ["b", "c"], "c": ["d"]}

{"a": ["b", "c"], "c": ["d"]}
```

Of course, you can use querystring and form data separately on POST and PUT requests.  
I just wanted to show an example of function signature accepting both GET, POST and PUT alongside with querystring and form data.

### JSON
In order for a route handler to get access to parsed json data,  
it must be explicitly set in the definition step of the route:

```python
import json

@app.route(path='/json', methods=['POST'], accepts=['json'])
def app_form(json):
  return json.dumps(json)
```

So, suppose we do a sequence of POST requests to this endpoint:

```
POST /json
{"a":1}
```

the results will be:

```
{"a": 1}
```

### Querystring + Form data + JSON + Path regex variables
In this example I want to show you how to use all of these features together:

```python
@app.route(path='/user/(?P<uid>\d+)/(?P<uname>\w+)', methods=['POST'], accepts=['querystring', 'form', 'json'])
def app_mixed(uid, uname, querystring, form, json):
  # do something
  pass
```

The route handler function signature must follow the variables priority.  
Path variables are passed first, from left to right (so, `uid` then `uname`);
accepted variables are passed later, from left to right (so, `querystring`, `form`, `json`);  
as show in the previous example.

### Response object
Until now, I only showed you how to return a string as a response (plus the http status code).  
String responses are internally wrapped into a `Response` object using `app.config["default_content_type"]` and `app.config["default_encoding"]` as default content type and encoding.

You can return a `Response` object directly from a route handler function and even extend it to define some custom response type.

In this repository you can find two additional `Response` objects: `JsonResponse` and `FileResponse` which are useful when you want to return a python dictionary and the content of a file respectively.

```python
from response import JsonResponse, FileResponse

@app.route(path='/favicon.ico', methods=['GET'])
def app_favicon():
  return FileResponse('static/favicon.ico', 'image/x-icon')
  
@app.route(path='/user/(?P<uid>\d+)/(?P<uname>\w+)', methods=['GET'])
def app_jres(uid, uname):
  return JsonResponse(dict(uid=uid, uname=uname))
```

You can introduce any `Response` object type you want by simply extending it.  
For instance it might be useful implementing a `TemplateResponse` that uses a template engine like jinja or whatever :)

### Handling HTTP errors (400, 404, 500, etc.)
In order to "gently" handle these erros, you must define an error handler, otherwise the server won't tell the browser some error occurred and close the connection immediatly.  
Internally a `NotImplementedError` exception will be raised to inform you to, possibly, define an error handler.

In order to register an error handler we must add an `ErrorRoute` route:

```python
@app.error(code='[45][0-9]{2}')
def error_4xx_5xx(code, **args):
	# code 400 and 500 may have an error argument
	# it's up to you to display it or not [e.g. when debugging]
	error = args.get('error', None)
	error = f'<pre><blockquote>{error}</blockquote></pre>' if error else ''

	return f'''
<!DOCTYPE html>
<html lang="en">
	<head>
		<meta charset="utf-8">
		<title>Error {code}</title>
	</head>
	<body>
		<p>Ops, an error #<strong>{code}</strong> occurred.</p>
		<p>{error}</p>
		<p>If the error persists, contact the administrator.</p>
	</body>
</html>
'''.strip(), code
```

As you can see, this is very similar to `@app.route`. The keyword argument `code` is compiled to a python regex as well, so you can match any error code you want to. Path variables (group symbolic names) will not be passed to the function handler, since they're not needed anyway.  
Function handlers for errors 400 (Bad Request), 404 (Not Found) and 500 (Internal server error) are internally looked up and defining them will allow you to gracefuly inform the browser (and the user) that some error occurred.

## Licensing
The source code of this project is released under GPLv3 license [[1]](LICENSE).  
 
## Warning
This project was done for educational purposes and for fun.  
Moreover, to quote python documentation:
> http.server is not recommended for production. It only implements basic security checks.

use at your own risk.
