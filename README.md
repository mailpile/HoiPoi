# Hoi Poi

Hoi Poi is a very light-weight, mostly-JS based user database which allows
users to vote on "issues". It was written for the Mailpile community
governance site.

The primary design goals were:

1. Simplicity
2. Minimal security footprint on the server
3. Minimal sysadmin overhead on the server
4. Ability for users to log in
5. Ability for logged in users to change their settings
6. Ability for logged in users to cast arbitrary votes on arbitrary issues

These goals are achieved by using 2 small CGI scripts, JSON and some clever
hashing instead of a proper database, and offloading all the heavy lifting
(not that there's much of it) to the Javascript and HTML code.


## Installation

On the server side:

1. Create a location for your user database:
   * It must be a static folder that is accessble using HTTP GET (over SSL)
   * Directory listings must be disabled (or drop in an empty index.html)
   * Directory permissions must allow the web server to read/write/execute
2. Enable CGI scripts on your web server
3. Copy `cgi-bin/user-mv.py` and `cgi-bin/user-up.py` to wherever your
   web server expects to find CGI scripts
4. Edit the CGI scripts so they know where the user database is
5. Copy the contents of the `js/` folder somewhere into your web site's
   static tree (we assume `/js/` in the examples below).


Your HTML code should then look something like this:

    <html>
    <head>
        ...

        <script src="/js/jquery.js"></script>
        <script src="/js/jquery.cookie.js"></script>
        <script src="/js/sha256.js"></script>
        <script src="/js/hoipoi.js"></script>
        <script>
            $(document).ready(function() {
                hoipoi.init();
            });
        </script>

        ...
    </head>
    <body>
        ...

        <div class="login-form">
            <b class="login-error">Login incorrect!</b>
            <input class="username"/>
            <input class="password" type="password"/>
            <button class="login">Log in</button>
        </div>
        <div class="logout-form">
            Hello, <span class='login-nickname'></span>
            <button class="logout">Log out</button>
        </div>

        ...

        <div class="vote-list">
            <div class="issue" data-issue="30201" data-options="yes,no">
                <span class="issue-title"><a href="https://github.com/pagekite/Mailpile/issues/30201">The name of the issue</a></span>
                <span class="issue-details">...</span>
            </div>
        </div>

        ...
     </body>
     </html>


## Scraping issues from Github

One way to generate a list of things for users to vote on, is to scrape
issues from Github.  An issue scraper is included in `cron/get-issues.py`,
which knows how to generate an HTML fragment formatted for use with Hoi Poi.

The issue scraper script relies on PyGithub:

    git clone https://github.com/jacquev6/PyGithub --branch develop_v2
    cd PyGithub
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt
    python setup.py install
    cd ..

You'll want to edit the script to point at your repo, instead of ours.


## Copyright & License

Copyright 2014, Bjarni R. Einarsson, Smári McCarthy, Mailpile ehf

Released under the MIT license.
