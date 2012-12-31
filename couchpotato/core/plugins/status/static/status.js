var StatusBase = new Class({

	setup: function(statuses){
		var self = this;

		self.statuses = statuses;

	},

	get: function(id){
		return this.statuses.filter(function(status){
			return status.id == id
		}).pick()
	},

	// Hide items when getting status
	getStatus: function(){
		return this.statuses.filter(function(status){
			return !status.hide
		});
	},
});
window.Status = new StatusBase();
