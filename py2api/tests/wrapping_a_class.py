import requests
from py2api.examples.wrapping_a_class import IntCalculator
from py2api.util import enhanced_docstr

port = 5003
root = 'http://0.0.0.0:{port}/'.format(port=port)
fullurl = lambda relurl: root + relurl

r = requests.get(fullurl('my_ws?attr=greet'))
assert r.json() == {'_result': 'Hello world!'}

r = requests.get(fullurl("my_ws?attr=greet&user=me"))
assert r.json() == {'_result': 'Hello me!'}

r = requests.get(fullurl("my_ws?attr=greet&dflt_greeting=Goodnight"))
assert r.json() == {'_result': 'Goodnight world!'}

r = requests.get(fullurl("my_ws?attr=greet&dflt_greeting=Goodnight&user=day"));
assert r.json() == {'_result': 'Goodnight day!'}

r = requests.get(fullurl("my_ws?attr=fcalc.whoami"));
assert r.json() == {'_result': 'a float calculator'}

r = requests.get(fullurl("my_ws?attr=icalc.compute&_help=1"))
assert r.text == enhanced_docstr(IntCalculator.compute)
# Will be something like...
# compute()

#         An int "x op y" operation (that is, division will be euclidean).
#         :param x: a number
#         :param op: the operation
#         :param y: another number
#         :return: the result of the operation

r = requests.get(fullurl("my_ws?attr=fcalc.compute&x=5&y=3&op=/"))
assert r.json() == {'_result': 1.6666666666666667}
r = requests.get(fullurl("my_ws?attr=icalc.compute&x=5&y=3&op=/"))
assert r.json() == {'_result': 1}
r = requests.get(fullurl("my_ws?attr=fcalc.compute&x=5&y=3&op=-"))
assert r.json() == {'_result': 2.0}
r = requests.get(fullurl("my_ws?attr=fcalc.compute&x=5&y=3&op=%2B"))
assert r.json() == {'_result': 8.0}

