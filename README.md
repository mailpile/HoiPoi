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
        <script src="/js/sjcl.js"></script>
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

        <div class="single-choice-election">
            <div class="issue" data-issue="30201" data-options="yes,no">
                <div class="vote-options"></div>
                <span class="issue-title"><a href="https://github.com/pagekite/Mailpile/issues/30201">The name of the issue</a></span>
                <span class="issue-details">...</span>
            </div>
            ...
        </div>

        ...

        <ol class="ranked-election">
            <li class="issue" data-issue="30201">
                <span class="issue-title"><a href="https://github.com/pagekite/Mailpile/issues/30201">The name of the issue</a></span>
                <span class="issue-details">...</span>
            </li>
            ...
        </ol>

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


## How it works/ed

These are mostly un-edited design notes for this little tool. They may be
a little bit out of date, but still mostly valid.

User database strategy:

* Give each backer a random auth token (24 bit random username, 72 bit random password -> hex 6 + 18 chars)
* User data is stored in filesystem as /some/folder/&lt;username>.&lt;sha256(&lt;username>, ":", &lt;password>)>.json
   * Initial user database is created with a python script that eats our list of backers and spits out json files
   * Mail them a "log in to your Mailpile Community" email with a magic clicable URL and username/password details
   * **Update:** Replaced SHA256 with 20149 rounds of PBKFD2 from the SJCL.
* When a user "logs in", javascript code calculates the path and downloads the JSON
   * On login, a cookie is set with the JSON filename value and the extracted user's name
   * The website UI can have trivial JS to say "Hello Person" and load the JSON on pages that need it
* The downloaded JSON contains a flat key -> value dictionary of things like:
    * nickname -> User's visible name, used in web UI, cookie and outgoing e-mail
    * email_subscription -> one of "weekly", "monthly", "none"
    * vote.ID -> one of "yes", "no", "none"
* When a user votes, an AJAX POST request is sent to /cgi-bin/user-up.py
    * Cookie is ignored for security reasons (avoid CSRF attacks)
    * json=JSON filename (slashes disallowed)
    * variable=vote.ID
    * value=yes (or no or none)
* Same interface is used to change name or e-mail subscription values
* When a user changes their password, an AJAX POST request is sent to /cgi-bin/user-mv.py
    * Cookie is ignored for security reasons (avoid CSRF attacks)
    * oldjson=JSON filename (slashes disallowed)
    * newjson=new JSON filename
* It is up to the javascript to calculate a new JSON filename using the same logic as it uses to convert passwords to JSON paths
* We should be able to write three python CGI scripts, under 100 lines each, no dependencies, no external database.
* Bonus fancy stuff:
   * CGI script for manually adding a user.
   * Special case in user-up.py for voting:
      * autogenerate a folder for each vote ID, with y and n subfolders. Script hard-links user JSON into subfolders for quick counting

Voting system strategy:

* Main community site is generated from the following bits:
   * Static template with friendly static content,
      * Manually curated questions
      * Link to daily snapshots
      * Twitter embedding box
      *  Recent blog post embedding box
   * Autogenerated roadmap
      * Cron job
      * Autogenerated from subset of github issues, listing issues with certain tags
      * Each issue, there is a vote up/down button, like hacker news
      * Javascript updates the CSS style of the button based on JSON
      * Clicking submits AJAX votes as described above


## Supported balloting methods

Hoipoi currently supports two balloting methods:

 * **Single choice ballots**, in which a user is presented with a set of options for each vote, of which one can be selected.
 * **Ranked ballots**, in which a user is presented with a set of options which can be arranged preferentially by dragging to sort.

## Supported tallying methods

Currently there is only one tallying method supplied, a Schulze Proportional Representation method for open sorting without cutoff. Requires Python Vote Core (pyvotecore) to work.


## Copyright & License

Copyright 2014, Bjarni R. Einarsson, Smári McCarthy, Mailpile ehf

Released under the MIT license.
