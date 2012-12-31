var StatsSettingTab = new Class({

	tab: '',
	content: '',

	initialize: function(){
		var self = this;

		App.addEvent('load', self.addSettings.bind(self))

	},

	addSettings: function(){
		var self = this;

		self.settings = App.getPage('Settings')
		self.settings.addEvent('create', function(){
			var tab = self.settings.createTab('stats', {
				'label': 'Statistics',
				'name': 'stats'
			});

			self.tab = tab.tab;
			self.content = tab.content;

			self.createstats();

		});

		self.settings.default_action = 'stats';

	},

	createstats: function(){
		var self = this;

		self.settings.createGroup({
			'label': 'Movie database statistics',
			'name': 'variables'
		}).inject(self.content).adopt(
			new Element('dl.info').adopt(
				new Element('dt[text=Wanted]'),
				self.wanted_text = new Element('dd', {
					'text': 'NB movies wanted',
					'events': {
						'mouseenter': function(){
							this.set('text', 'Calculating Wanted...')
						},
						'mouseenter': function(){
							self.fillWanted('wanted')
						}
					}
				}),
				new Element('dt[text=Snatched]'),
				self.snatched_text = new Element('dd', {
					'text': 'NB movies snatched',
					'events': {
						'mouseenter': function(){
							this.set('text', 'Calculating Snatched...')
						},
						'mouseenter': function(){
							self.fillSnatched('snatched')
						}
					}
				}),
				new Element('dt[text=Done]'),
				self.done_text = new Element('dd', {
					'text': 'NB movies done',
					'events': {
						'mouseenter': function(){
							this.set('text', 'Calculating Done...')
						},
						'mouseenter': function(){
							self.fillDone('done')
						}
					}
				}),
				new Element('dt[text=Viewed]'),
				self.viewed_text = new Element('dd', {
					'text': 'NB movies viewed',
					'events': {
						'mouseenter': function(){
							this.set('text', 'Calculating Viewed...')
						},
						'mouseenter': function(){
							self.fillViewed('viewed')
						}
					}
				}),
				new Element('dt[text=Deleted]'),
				self.deleted_text = new Element('dd', {
					'text': 'NB movies deleted',
					'events': {
						'mouseenter': function(){
							this.set('text', 'Calculating Deleted...')
						},
						'mouseenter': function(){
							self.fillstats('deleted')
						}
					}
				})
			)
		);

	},

	fillstats: function(status){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': status
			},
			'onSuccess': function(responseJSON, responseText){
				self.deleted_text.set('text', responseJSON.total + ' ' + status);
			}
		});
	},

	fillWanted: function(){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': 'active'
			},
			'onSuccess': function(responseJSON, responseText){
				self.wanted_text.set('text', responseJSON.total + ' wanted');
			}
		});
	},

	fillSnatched: function(){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': 'snatched'
			},
			'onSuccess': function(responseJSON, responseText){
				self.snatched_text.set('text', responseJSON.total + ' snatched');
			}
		});
	},

	fillDone: function(){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': 'done'
			},
			'onSuccess': function(responseJSON, responseText){
				self.done_text.set('text', responseJSON.total + ' done');
			}
		});
	},

	fillViewed: function(){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': 'viewed'
			},
			'onSuccess': function(responseJSON, responseText){
				self.viewed_text.set('text', responseJSON.total + ' viewed');
			}
		});
	},

	fillDeleted: function(){
		var self = this;
		Api.request('movie.list', {
			'data': {
				'status': 'deleted'
			},
			'onSuccess': function(responseJSON, responseText){
				self.deleted_text.set('text', responseJSON.total + ' deleted');
			}
		});
	}

});

window.addEvent('domready', function(){
	new StatsSettingTab();
});
