/* The Javascript part of the Minimum Viable User Database, With Voting
 *
 * This drops into pretty much any HTML page and can be configured to
 * display and register votes on whatever.
 */

hoipoi = (function() {

    // This adds python-style %(name)s placeholder replacement to the
    // standard string class.
    String.prototype.pyformat = function(vars) {
        return this.replace(/\%\(([a-zA-Z_-]+)\)s/g, function(group, name) {
            return vars[name];
        });
    };

    // This is a lossy encoding that will only modify the string once, no
    // matter how often you encode it. It is also guaranteed not to get
    // decoded by standard parts of a normal web stack.
    var _encode_once = function(txt) {
        return encodeURIComponent(txt).replace(/%([a-fA-F0-9][a-fA-F0-9])/g,
                                               function(_, pair) {
            return "-" + pair.toUpperCase();
        });
    };

    // Partial reversal of the above - just to make e-mail addresses look
    // nice. Does NOT decode all cases.
    var _decode_some = function(txt) {
        return txt.replace(/-40/g, "@").replace(/-2B/g, "+");
    };

    // Magic cookies that can also come from URL hash parts!
    var _hashbrownie = function(name) {
        var hash = "&" + (document.location.hash || "#").substring(1);
        var find = "&" + name + "=";
        var where = hash.indexOf(find);
        if (where >= 0) {
            var val = hash.substring(where + find.length);
            where = val.indexOf("&");
            if (where >= 0) {
                return _decode_some(val.substring(0, where));
            }
            return _decode_some(val);
        }
        return $.cookie(name);
    };

    var _cache_bust = function(url) {
        var ts = (new Date()).getTime();
        if (url.indexOf("?") < 0) {
            return url + "?_cts=" + ts;
        }
        else {
            return url + "&_cts=" + ts;
        }
    };

    return {
        default_site_info: {
            // Default settings...
            url_db: "/hoipoi/db/",       // Directory of user json
            url_up: "/cgi-bin/user-up.py",   // Path to update CGI script
            url_mv: "/cgi-bin/user-mv.py",   // Path to moving CGI script
            url_mk: "/cgi-bin/user-mk.py",   // Path to creating CGI script
            dom_login: ".login-form",        // Selector for login form
            dom_logout: ".logout-form",      // Selector for logout form
            dom_login_error: ".login-error", // Selector for "login failed"
            dom_nickname: ".login-nickname", // Selector for user's name
            cookie_user: "username",         // Cookie to store user name
            cookie_token: "token",           // Cookie to store token

            // Python-string style template for a voting button
            pyformat_vote: ("<a class='vote vote-%(vote)s' " +
                            "   id='%(id)s' " +
                            "   data-issue='%(issue)s' " +
                            "   data-value='%(vote)s'>%(vote)s</a>"),

            // Callbacks for specific events
            callback_login_ok: null,
            callback_login_error: null,
            callback_logged_out: null,
            callback_single_vote_ok: null,
            callback_single_vote_error: null,
            callback_ranked_vote_ok: null,
            callback_ranked_vote_error: null
        },
        username: null,
        token: null,
        userinfo: {},

        make_token: function(username, password) {
            var pbkdf2 = sjcl.misc.pbkdf2(password, username, 20149, 128);
            return sjcl.codec.hex.fromBits(pbkdf2);
        },

        make_url: function(path, username, token) {
            username = _encode_once(username || this.username);
            token = (token || this.token);
            return (path +
                    '#' + this.site_info.cookie_user + '=' + username +
                    '&' + this.site_info.cookie_token + '=' + token);
        },

        // This function installs the required hooks for login/logout
        // and checks the current cookie state to figure out whether
        // we're logged in or not.
        init: function(site_info) {
            this.site_info = {};
            for (attr in this.default_site_info) {
                this.site_info[attr] = ((site_info && site_info[attr]) ||
                                        this.default_site_info[attr]);
            }
            this.username = _hashbrownie(hoipoi.site_info.cookie_user);
            this.token = _hashbrownie(hoipoi.site_info.cookie_token);

            // Set some common DOM elements
            $(this.site_info.dom_login + " .username").val(this.username);
            $(this.site_info.dom_login_error).hide();

            // Set our form handlers
            $(this.site_info.dom_login + " button").click(function() {
                var u = $(hoipoi.site_info.dom_login + " .username").val();
                var p = $(hoipoi.site_info.dom_login + " .password").val();
                hoipoi.login(u, p);
                return false;
            });
            $(this.site_info.dom_logout + " button").click(function() {
                hoipoi.logout();
                return false;
            });

            if (this.username && this.token) {
                // If we have a token cookie, try to log in.
                this._load_userinfo();
            }
            else {
                // Otherwise, just show the login form
                $(this.site_info.dom_logout).hide();
                $(this.site_info.dom_login_error).hide();
                $(this.site_info.dom_login).show();
            }
        },

        json_path: function(username, token) {
            return _encode_once((username || this.username) + "." +
                                (token || this.token) + ".json");
        },

        _clear_cookies: function() {
            $.cookie(hoipoi.site_info.cookie_user, "", {expires: 0});
            $.cookie(hoipoi.site_info.cookie_token, "", {expires: 0});
        },

        _clear_userinfo: function() {
            $(hoipoi.site_info.dom_login + " .password").val("");
            hoipoi.token = null;
            hoipoi.username = null;
            hoipoi.userinfo = {};
            hoipoi.remove_vote_buttons();
        },

        _login_ok: function(userdata) {
            hoipoi.userinfo = userdata;
            $(hoipoi.site_info.dom_login_error).hide();
            $(hoipoi.site_info.dom_logout).show();
            $(hoipoi.site_info.dom_login).hide();
            $(hoipoi.site_info.dom_nickname).html(userdata.nickname);
            $.cookie(hoipoi.site_info.cookie_user, hoipoi.username);
            $.cookie(hoipoi.site_info.cookie_token, hoipoi.token,
                     {expires: 10});
            hoipoi.create_elections();
        },

        _login_succeeded: function(userdata) {
            hoipoi._login_ok(userdata);
            if (hoipoi.site_info.callback_login_ok) {
                hoipoi.site_info.callback_login_ok();
            };
        },

        _login_failed: function() {
            $(hoipoi.site_info.dom_logout).hide();
            $(hoipoi.site_info.dom_login).show();
            $(hoipoi.site_info.dom_login_error).show();
            hoipoi._clear_cookies();
            if (hoipoi.site_info.callback_login_error) {
                hoipoi.site_info.callback_login_error();
            };
        },

        _load_userinfo: function() {
            $.ajax({
                url: _cache_bust(this.site_info.url_db + this.json_path()),
                type: "GET",
                success: this._login_succeeded,
                error: this._login_failed
            });
        },

        login: function(username, password) {
            var token = this.make_token(username, password);
            this.token = token;
            this.username = username;
            this._load_userinfo();
        },

        logout: function(username, password) {
            $(this.site_info.dom_logout).hide();
            $(this.site_info.dom_login).show();
            $(this.site_info.dom_login_error).hide();
            this._clear_userinfo();
            this._clear_cookies();
            if (hoipoi.site_info.callback_logout) {
                hoipoi.site_info.callback_logout();
            };
        },

        user_set: function(variable, value, ok, fail) {
            $.ajax({
                url: this.site_info.url_up,
                type: "POST",
                data: {
                    json: this.json_path(),
                    variable: variable,
                    value: value
                },
                success: function(userdata) {
                    hoipoi._login_succeeded(userdata);
                    if (ok) { ok(); }
                },
                error: fail
            });
        },

        change_username_password: function(username, password, ok, fail) {
            var token = this.make_token(username, password);
            $.ajax({
                url: this.site_info.url_mv,
                type: "POST",
                data: {
                    oldjson: this.json_path(),
                    newjson: this.json_path(username, token)
                },
                success: function(userdata) {
                    $(hoipoi.site_info.dom_login + " .username"
                      ).val(this.username);
                    hoipoi.token = token;
                    hoipoi.username = username;
                    hoipoi._login_succeeded(userdata);
                    if (ok) { ok(); }
                },
                error: fail
            });
        },

        user_create: function(auth, json_path, content,
                              mailto, password, login_url,
                              ok, fail) {
            $.ajax({
                url: this.site_info.url_mk,
                type: "POST",
                data: {
                    auth: auth,
                    json: json_path,
                    content: JSON.stringify(content),
                    mailto: mailto,
                    password: password,
                    login_url: login_url
                },
                success: ok,
                error: fail
            });
        },

        /**** Voting code follows *******************************************/

        create_elections: function() {
            hoipoi.create_ranked_elections();
            hoipoi.create_single_choice_elections();
        },

        create_ranked_elections: function() {
            $(".ranked-election").each(function(index, element) {
                var e = $(element);
                var eid = e.data("election");
                console.log("Initializing ranked election " + eid);
                if (hoipoi.userinfo["election."+eid]) {
                    // We have ballot data for this election!
                    var order = hoipoi.userinfo["election."+eid].split(",");
                    console.log("Found user preferences for election: ", order);
                    function sort_li(a, b) {
                        a = $(a).data("issue").toString();
                        b = $(b).data("issue").toString();
                        return (order.indexOf(a) > order.indexOf(b)) ? 1 : -1;
                    }
                    e.children().sort(sort_li).appendTo(element);
                }
                console.log("Making ranked election sortable");
                e.sortable({
                    onDrop: function(item) {
                        var val = 0;
                        var issue_order = [];
                        election = $(item).parent();
                        election.children().each(function(i, e) {
                            var m = $(e);
                            issue_order.push(m.data("issue"));
                        });
                        var e = election.data("election");
                        hoipoi.user_set("election." + e, issue_order.join(","),
                            hoipoi.site_info.callback_ranked_vote_ok,
                            hoipoi.site_info.callback_ranked_vote_error
                        );
                        election.addClass("updating");
                        item.removeClass("dragged").removeAttr("style");
                        $("body").removeClass("dragging")
                        return true;
                    }
                });
                e.removeClass("updating");
            });
        },

        create_single_choice_elections: function() {
            $(".single-choice-election").find(".issue").each(function(i, e) {
                var m = $(e);
                var issue = m.data("issue");
                var options = (m.data("options") || "yes,no").split(",");
                for (o in options) {
                    var val = options[o];
                    var aid = "vote-" + issue + "-" + val;
                    if (!$("#"+aid).length) {
                        m.append(hoipoi.site_info.pyformat_vote.pyformat({
                            id: aid,
                            vote: val,
                            issue: issue
                        }));
                        $("#"+aid).click(function(e) {
                            var issue = $(e.target).data("issue");
                            var value = $(e.target).data("value");
                            $(e.target).addClass("selecting");
                            if ($(e.target).hasClass("selected")) {
                                value = "";
                            }
                            hoipoi.cast_vote(issue, value);
                        });
                    }
                }
            });

            $(".vote").removeClass("selected").removeClass("selecting");
            for (i in this.userinfo) {
                if (i.indexOf("vote") == 0) {
                    var issue = i.substring(5);
                    var val = this.userinfo[i];
                    var aid = "vote-" + issue + "-" + val;
                    $("#"+aid).addClass("selected");
                }
            }
        },

        remove_vote_buttons: function() {
            $(".vote").remove();
        },

        cast_vote: function(issue, vote) {
            this.user_set("vote." + issue, vote,
                hoipoi.site_info.callback_single_vote_ok,
                hoipoi.site_info.callback_single_vote_error
            );
        }
    };
})();
