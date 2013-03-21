Page.Queue = new Class({

	Extends: PageBase,

	name: 'queue',
	title: 'Movie waiting!',

	indexAction: function(param){
		var self = this;

		if(!self.list){
			self.refresh_button = new Element('a', {
				'title': 'Rescan your library for new movies',
				'text': 'Full library refresh',
				'events':{
					'click': self.refresh.bind(self, true)
				}
			});

			self.refresh_quick = new Element('a', {
				'title': 'Just scan for recently changed',
				'text': 'Quick library scan',
				'events':{
					'click': self.refresh.bind(self, false)
				}
			});

			self.list = new MovieList({
				'identifier': 'queue',
				'status': 'snatched',
				'actions': [MA.IMDB, MA.ALLOCINE, MA.SENSACINE, MA.Trailer, MA.Files, MA.Readd, MA.Edit, MA.Delete, MA.Status],
				'menu': [self.refresh_button, self.refresh_quick],
				'on_empty_element': App.createUserscriptButtons().addClass('empty_wanted')
			});
			$(self.list).inject(self.el);

			// Check if search is in progress
			self.startProgressInterval();
		}

	},

	refresh: function(full){
		var self = this;

		if(!self.update_in_progress){

			Api.request('queue.update', {
				'data': {
					'full': +full
				}
			})

			self.startProgressInterval();

		}

	},

	startProgressInterval: function(){
		var self = this;

		self.progress_interval = setInterval(function(){

			Api.request('queue.progress', {
				'onComplete': function(json){
					self.update_in_progress = true;

					if(!json || !json.progress){
						clearInterval(self.progress_interval);
						self.update_in_progress = false;
						if(self.progress_container){
							self.progress_container.destroy();
							self.list.update();
						}
					}
					else {
						if(!self.progress_container)
							self.progress_container = new Element('div.progress').inject(self.list.navigation, 'after')

						self.progress_container.empty();

						Object.each(json.progress, function(progress, folder){
							new Element('div').adopt(
								new Element('span.folder', {'text': folder}),
								new Element('span.percentage', {'text': progress.total ? (((progress.total-progress.to_go)/progress.total)*100).round() + '%' : '0%'})
							).inject(self.progress_container)
						});

					}
				}
			})

		}, 1000);

	}

});
