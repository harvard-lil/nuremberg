modulejs.define('DraggingMixin', function () {
  return {
    events: {
      'mousedown': 'startDrag',
    },
    startDrag: function (e) {
      if (e.which !== 1 || (e.which !== 3 && this.model.attributes.tool !== 'magnify'))
        return;
      this.model.set('dragPosition', {x: e.clientX, y: e.clientY});
      $(document).on('mousemove', this.doDrag);
      $(document).one('mouseup', this.endDrag);
      e.preventDefault();
    },
    endDrag: function (e) {
      this.model.set('dragPosition', null);
      $(document).off('mousemove', this.doDrag);
    },
    doDrag: function (e) {
      var oldPosition = this.model.get('dragPosition');
      var newPosition = {x: e.clientX, y: e.clientY};
      this.$el.scrollLeft(this.$el.scrollLeft() + oldPosition.x - newPosition.x);
      this.$el.scrollTop(this.$el.scrollTop() + oldPosition.y - newPosition.y);
      this.model.set('dragPosition', newPosition);
    },
    mixin: function (view) {
      _.defaults(view.prototype, this);
      _.defaults(view.prototype.events, this.events);
      var _initialize = view.prototype.initialize;
      view.prototype.initialize = function () {
        _initialize.call(this);
        _.bindAll(this, 'startDrag', 'endDrag', 'doDrag');
      };
    },
  };
});
