
votes = {
	userinfo: null,

	init: function() {
		// Initialize all the things
		$("#login-username").val($.cookie("username"));
		if ($.cookie("token")) {
			// Refresh the cookie
			$.cookie("token", $.cookie("token"), {expires: 10});
		}

		$("#login-button").click(function() {
			var user = $("#login-username").val();
			var pass = $("#login-password").val();
			votes.login(user, pass)
;		});

		$("#login-button").click(function() {
			votes.logout();
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
		$.getJSON("/vote", params, callback);
	},

	warning: function(msg) {
		alert(msg);
	},
};



$(function() {
	votes.init();
});