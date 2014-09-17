
votes = {
	userinfo: {},

	init: function() {
		// Initialize all the things
		$("#login-username").val($.cookie("username"));
		if ($.cookie("token")) {
			// Refresh the cookie
			$.cookie("token", $.cookie("token"), {expires: 10});
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

		$(".vote").click(function(e) {
			var issue = $(e.target).data("issue");
			var value = $(e.target).data("value");
			votes.cast_vote(issue, value);
		});

	},

	login: function(username, password) {
		console.log("Attempting to log in...");
		var token = Sha256.hash(username + ":" + password);
		votes.token = token;
		votes.username = username;
		$.getJSON("mvuserdb/" + username + "." + token + ".json", function(data) {
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

	update_path: function(key, value) {
		votes.userinfo[key] = value;
		$.getJSON("https://www.mailpile.is/cgi-bin/mailpile/user-up.py", {key: value}, function(data) {
			// pass
		});
	},

	set_path: function(username, password) {
		$.getJSON("https://www.mailpile.is/cgi-bin/mailpile/user-mv.py", {}, function() {

		});
	},


	warning: function(msg) {
		alert(msg);
	},
};



$(function() {
	votes.init();
});