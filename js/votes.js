
votes = {
	userinfo: {},

	init: function() {
		// Initialize all the things
		$("#login-username").val($.cookie("username"));
		if ($.cookie("token")) {
			// Refresh the cookie
			$.cookie("token", $.cookie("token"), {expires: 10});
			votes.create_votebuttons();
			$(".vote").show();
		}

		$("#login-button").click(function() {
			var user = $("#login-username").val();
			var pass = $("#login-password").val();
			votes.login(user, pass);
		});

		$("#login-button").click(function() {
			votes.logout();
		});
	},

	login: function(username, password) {
		console.log("Attempting to log in...");
		var token = Sha256.hash(username + ":" + password);
		votes.token = token;
		votes.username = username;
		$.getJSON("mvuserdb/" + votes.jsonpath(), function(data) {
			if (data) {
				votes.userinfo = data;
				$.cookie("username", username);
				$.cookie("token", token, {expires: 10});
				$(".vote").show();
				console.log("Logged in.");
			} else {
				votes.warning("Invalid user name or password");
			}
		});

		votes.create_votebuttons();
	},

	create_votebuttons: function() {
		$(".issue").each(function(i, e) {
			var m = $(e);
			var issue = m.data("issue");
			var options = (m.data("options") || "yes,no").split(",");
			for (o in options) {
				var val = options[o];
				m.append("<a class=\"vote\" data-issue=\"" + issue + "\" data-value=\"" + val + "\">" + val + "</a>");
			}
		});

		for (i in votes.userinfo) {
			if (i.indexOf("vote") == 0) {
				matchers =   "data-issue=" + issue;
				$(".vote["+matchers).removeClass("selected");
				matchers += ",data-value=" + votes.userinfo[i];
				$(".vote["+matchers).addClass("selected");
			}
		}

		$(".vote").click(function(e) {
			var issue = $(e.target).data("issue");
			var value = $(e.target).data("value");
			votes.cast_vote(issue, value);
		});
	},

	logout: function() {
		votes.userinfo = null;
		$.cookie("username", "");
		$.cookie("token", "");
	},

	cast_vote: function(issue, vote) {
		console.log("Casting vote of " + vote + " to issue " + issue);
		votes.update_path("vote." + issue, vote);
	},

	jsonpath: function() {
		return votes.username + "." + votes.token + ".json";
	},

	update_path: function(key, value) {
		votes.userinfo[key] = value;
		$.getJSON("https://www.mailpile.is/cgi-bin/mailpile/user-up.py", 
			{json: votes.jsonpath(), variable: key, value: value},
			function(data) {
				// pass
			}
		);
	},

	set_path: function(username, password) {
		$.getJSON("https://www.mailpile.is/cgi-bin/mailpile/user-mv.py", {}, function(data) {
			if (data) {

			}
		});
	},


	warning: function(msg) {
		alert(msg);
	},
};



$(function() {
	votes.init();
});