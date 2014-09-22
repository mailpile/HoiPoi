#!/usr/bin/python
#
# This script will act as a cgi-bin script, accepting POST requests of the
# form:
#
#   json=JSON filename (slashes disallowed)
#   auth=<something>
#   content=<JSON-formatted-content>
#
# Further optional POST variables:
#
#   mailto=<email>
#   password=<password>
#   login_url=<auto-login URL>
#
# If the named JSON file does not exist, it will be created with the contents
# specified. The auth variable must match the password which is hard-coded
# into the script.
#
# If that all goes well and the optional variables are provided, the user
# will be e-mailed an invitation to log in to their brand new account.
#
import cgi
import os
import json
import sys
from hashlib import sha256
from subprocess import Popen, PIPE


# This defaults to "Testing Hoi Poi", please change to something else.
AUTH_SALT = '00000000'
AUTH_HASH = '067aa95faacc9a3e4fa00b69860bb08a95eceea3ec102d12b9ffb4096a144165'
EMAIL_TPL = '/home/mailpile/hoipoi/invite.txt'
JSON_HOME = '/home/mailpile/hoipoi/db/'


created = None
try:
    assert(os.getenv('REQUEST_METHOD') == 'POST')

    request = cgi.FieldStorage()

    # Authenticate before doing any more work
    auth = unicode(request['auth'].value)
    assert(sha256(AUTH_SALT + auth).hexdigest() == AUTH_HASH)

    # Load up all our data
    json_file = str(request['json'].value)
    content = unicode(request['content'].value)
    if 'mailto' in request:
        mailto = unicode(request['mailto'].value)
        password = unicode(request['password'].value)
        login_url = unicode(request['login_url'].value)
        email_template = open(EMAIL_TPL, 'r').read()
        email_subject, email_body = email_template.split('\n\n', 1)
        assert(email_subject.lower().startswith('subject:'))
        email_subject = email_subject.split(':', 1)[1].strip()
    else:
        mailto = password = login_url = None
        email_subject = email_body = email_template = None

    # Sanity check the data
    userdata = json.loads(content)
    content = json.dumps(userdata)
    assert('/' not in json_file)
    assert(json_file.endswith('.json'))
    json_path = os.path.join(JSON_HOME, json_file)
    assert(not os.path.exists(json_path))
    if mailto:
        assert('@' in mailto)
        assert(login_url.startswith('http'))

    # Create new user's JSON file
    with open(json_path, 'w') as fd:
        fd.write(content)
        created = json_path

    # Send the user an invitation
    if mailto:
        nickname = userdata.get('nickname', mailto)
        def fmt(txt):
            return txt % {
                'nickname': nickname,
                'password': password,
                'mailto': mailto,
                'login_url': login_url
            }
        email_subject = fmt(email_subject)
        email_body = fmt(email_body)
        mailer = Popen(['mutt', '-s', email_subject, mailto],
                       stdin=PIPE, stdout=PIPE, stderr=PIPE)
        mailer.stdin.write(email_body)
        mailer.stdin.close()
        sys.stderr.write(mailer.stdout.read())
        sys.stderr.write(mailer.stderr.read())
        assert(0 == mailer.wait())

    print 'Content-type: application/json'
    print
    print '%s' % content

except:
    import traceback
    sys.stderr.write(traceback.format_exc())
    if created is not None:
        os.remove(created)
    print 'Content-type: text/plain'
    print 'Status: 500'
    print
    print 'Internal Scripting Fudge'
