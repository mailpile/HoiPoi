/* The Javascript part of the Minimum Viable User Database, With Voting
 *
 * This drops into pretty much any HTML page and can be configured to
 * display and register votes on whatever.
 */
mvuserdbwv = (function() {
    return {
        site_info: {
            // Default settings...
            url_db: "/mvuserdbwv/db/",       // Directory of user json
            url_up: "/cgi-bin/user-up.py",   // Path to update CGI script
            url_mv: "/cgi-bin/user-mv.py",   // Path to moving CGI script
            dom_login: ".login-form",        // Selector for login form
            dom_logout: ".logout-form",      // Selector for logout form
            dom_login_error: ".login-error", // Selector for "login failed"
            dom_nickname: ".login-nickname", // Selector for user's name
            cookie_user: "username",         // Cookie to store user name
            cookie_token: "token"            // Cookie to store token
        },
        username: null,
        token: null,
        userinfo: {},

        // This function installs the required hooks for login/logout
        // and checks the current cookie state to figure out whether
        // we're logged in or not.
        init: function(site_info) {
            if (site_info) {
                this.site_info = site_info;
            }
            this.username = $.cookie(mvuserdbwv.site_info.cookie_user);
            this.token = $.cookie(mvuserdbwv.site_info.cookie_token);

            // Set some common DOM elements
            $(this.site_info.dom_login + " .username").val(this.username);
            $(this.site_info.dom_login_error).hide();

            // Set our form handlers
            $(this.site_info.dom_login + " button").click(function() {
                var u = $(mvuserdbwv.site_info.dom_login + " .username").val();
                var p = $(mvuserdbwv.site_info.dom_login + " .password").val();
                mvuserdbwv.login(u, p);
                return false;
            });
            $(this.site_info.dom_logout + " button").click(function() {
                mvuserdbwv.logout();
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
            return ((username || this.username) + "." +
                    (token || this.token) + ".json");
        },

        _clear_cookies: function() {
            $.cookie(mvuserdbwv.site_info.cookie_user, "", {expires: 0});
            $.cookie(mvuserdbwv.site_info.cookie_token, "", {expires: 0});
        },

        _clear_userinfo: function() {
            $(mvuserdbwv.site_info.dom_login + " .password").val('');
            mvuserdbwv.token = null;
            mvuserdbwv.username = null;
            mvuserdbwv.userinfo = {};
            mvuserdbwv.remove_vote_buttons();
        },

        _login_succeeded: function(userdata) {
            mvuserdbwv.userinfo = userdata;
            $(mvuserdbwv.site_info.dom_login_error).hide();
            $(mvuserdbwv.site_info.dom_logout).show();
            $(mvuserdbwv.site_info.dom_login).hide();
            $(mvuserdbwv.site_info.dom_nickname).html(userdata.nickname);
            $.cookie(mvuserdbwv.site_info.cookie_user, mvuserdbwv.username);
            $.cookie(mvuserdbwv.site_info.cookie_token, mvuserdbwv.token,
                     {expires: 10});
            mvuserdbwv.create_vote_buttons();
        },

        _login_failed: function() {
            $(mvuserdbwv.site_info.dom_logout).hide();
            $(mvuserdbwv.site_info.dom_login).show();
            $(mvuserdbwv.site_info.dom_login_error).show();
            mvuserdbwv._clear_cookies();
        },

        _load_userinfo: function() {
            $.ajax({
                url: this.site_info.url_db + this.json_path(),
                type: 'GET',
                dataType: 'json',
                success: this._login_succeeded,
                error: this._login_failed
            });
        },

        login: function(username, password) {
            var token = Sha256.hash(username + ":" + password);
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
        },

        user_set: function(variable, value, ok, fail) {
            $.ajax({
                url: this.site_info.url_up,
                type: 'POST',
                data: {
                    json: this.json_path(),
                    variable: variable,
                    value: value
                },
                success: function(userdata) {
                    mvuserdbwv._login_succeeded(userdata);
                    if (ok) { ok(); }
                },
                error: fail
            });
        },

        change_username_password: function(username, password, ok, fail) {
            var token = Sha256.hash(username + ":" + password);
            $.ajax({
                url: this.site_info.url_mv,
                type: 'POST',
                dataType: 'json',
                data: {
                    oldjson: this.json_path(),
                    newjson: this.json_path(username, token)
                },
                success: function(userdata) {
                    $(mvuserdbwv.site_info.dom_login + " .username"
                      ).val(this.username);
                    mvuserdbwv.token = token;
                    mvuserdbwv.username = username;
                    mvuserdbwv._login_succeeded(userdata);
                    if (ok) { ok(); }
                },
                error: fail
            });
        },

        /**** Voting code follows *******************************************/

        create_vote_buttons: function() {
            $(".issue").each(function(i, e) {
                var m = $(e);
                var issue = m.data("issue");
                var options = (m.data("options") || "yes,no").split(",");
                for (o in options) {
                    var val = options[o];
                    var aid = "vote-" + issue + "-" + val;
                    if (!$("#"+aid).length) {
                        m.append("<a class=\"vote vote-" + val + "\"" +
                                 "   id=\"" + aid + "\"" +
                                 "   data-issue=\"" + issue + "\"" +
                                 "   data-value=\"" + val + "\">" + val + "</a>");
                        $("#"+aid).click(function(e) {
                            var issue = $(e.target).data("issue");
                            var value = $(e.target).data("value");
                            $(e.target).addClass("selecting");
                            if ($(e.target).hasClass("selected")) {
                                value = "";
                            }
                            mvuserdbwv.cast_vote(issue, value);
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
            this.user_set("vote." + issue, vote);
        }
    };
})();
