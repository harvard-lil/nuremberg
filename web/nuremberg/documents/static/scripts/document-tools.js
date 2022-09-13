modulejs.define('DocumentTools', function () {
  var ViewModel = Backbone.Model.extend({});

  return ToolbarView = Backbone.View.extend({
    initialize: function () {
      _.bindAll(this, 'setPage');
      var view = this;

      this.model = new ViewModel({page: 1});

      this.model.attributes.firstPage = view.$el.find('option').first().val();
      this.model.attributes.lastPage = view.$el.find('option').last().val();

      this.on('goToPage', function (page) {
        view.model.set('page', Math.min(Math.max(page, view.model.attributes.firstPage), view.model.attributes.lastPage));
        if (view.$el.find('option[value='+page+']').length)
          view.$el.find('select').val(page);
      });
    },
    events: {
      'click .zoom-in': function () { this.trigger('zoomIn'); },
      'click .zoom-out': function () { this.trigger('zoomOut'); },
      'click .next-page': function () { this.trigger('goToPage', this.model.get('page') + 1); },
      'click .prev-page': function () { this.trigger('goToPage', this.model.get('page') - 1); },
      'click .first-page': function () { this.trigger('goToPage', this.model.get('firstPage')); },
      'click .last-page': function () { this.trigger('goToPage', this.model.get('lastPage')); },
      'change select': function (e) { this.trigger('goToPage', e.target.value); },

      'click .tool-buttons .magnify': function () { this.trigger('setTool', 'magnify'); return false; },
      'click .tool-buttons .scroll': function () { this.trigger('setTool', 'scroll'); return false; },
      'click .tool-buttons .expand': function () { this.trigger('toggleExpand'); return false; },
    },
    setPage: function (page) {
      this.model.set('page', page);
      this.$el.find('select').val(page);
    },
    setPageDownload: function (url, filename) {
      this.$el.find('.download-page')
      .attr('href', url)
      .attr('download', filename);
    }
  });
});
