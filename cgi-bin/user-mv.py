#!/usr/bin/python
#
# This script will act as a cgi-bin script, accepting POST requests of the
# form:
#
#   oldjson=JSON filename (slashes disallowed)
#   newjson=JSON filename (slashes disallowed)
#
# If the named JSON file exists, it will be renamed to use the new name.
#
import cgi
import os
import json
import sys

JSON_HOME = '/home/mailpile/mvuserdb/'

try:
    assert(os.getenv('REQUEST_METHOD') == 'POST')

    request = cgi.FieldStorage()
    json_old = str(request['oldjson'].value)
    json_new = str(request['newjson'].value)
    assert('/' not in json_old)
    assert('/' not in json_new)

    json_old_path = os.path.join(JSON_HOME, json_old)
    json_new_path = os.path.join(JSON_HOME, json_new)

    assert(os.path.exists(json_old_path))
    assert(not os.path.exists(json_new_path))
    os.rename(json_old_path, json_new_path)

    print 'Content-type: application/json'
    print
    print '%s' % open(json_new_path).read()

except:
    import traceback
    sys.stderr.write(traceback.format_exc())
    print 'Content-type: text/plain'
    print 'Status: 500'
    print
    print 'Internal Scripting Fudge'
