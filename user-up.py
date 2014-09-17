#!/usr/bin/python
#
# This script will act as a cgi-bin script, accepting POST requests of the
# form:
#
#   json=JSON filename (slashes disallowed)
#   variable=<something>
#   value=<something>
#
# If the named JSON file exists, it will be edited to update the named
# variable with the requested value.  It will then return the contents of
# the updated JSON file as output.
#
import cgi
import os
import json
import sys

JSON_HOME = '/home/mailpile/mvuserdb/'

try:
    assert(os.getenv('REQUEST_METHOD') == 'POST')

    request = cgi.FieldStorage()
    json_file = str(request['json'].value)
    variable = unicode(request['variable'].value)
    value = unicode(request['value'].value)

    assert('/' not in json_file)
    json_path = os.path.join(JSON_HOME, json_file)

    data = json.load(open(json_path, 'r'))
    data[variable] = value
    json.dump(data, open(json_path, 'w'))

    print 'Content-type: application/json'
    print
    print '%s' % data

except:
    import traceback
    sys.stderr.write(traceback.format_exc())
    print 'Content-type: text/plain'
    print 'Status: 500'
    print
    print 'Internal Scripting Fudge'
