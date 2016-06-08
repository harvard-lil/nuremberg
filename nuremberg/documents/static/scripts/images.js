modulejs.define('Images', function () {
  var Images = {
    Model: Backbone.Model.extend({
      defaults: {
        scale: 1,
        visible: false,
        preloaded: false,
        loader: null
      },
      initialize: function () {
        _.bindAll(this, 'handleVisible', 'xhrProgress');

        this.on('change:visible', this.handleVisible);
        this.attributes.cache = {};
      },

      xhrProgress: function (e) {
        this.set('percentLoaded', (e.loaded / (e.total || 150 * 1024)) * 100);
      },

      handleVisible: function () {
        var model = this;
        _.defer(function () {
          if (model.get('visible')) {
            var scale = model.attributes.scale;
            if (scale < 0.25) {
              model.preloadImage('thumb');
            } else if (scale < 0.50) {
              model.preloadImage('half');
            } else if (scale < 1.50) {
              model.preloadImage('screen');
            } else {
              model.preloadImage('full');
            }
          } else {
            if (model.attributes.loader) {
              model.attributes.loader.abort();
              model.set('loader', null);
            }
          }
        });
      },

      hardload: function (size) {
        var sizes = ['thumb', 'half', 'screen', 'full'];
        var url;
        for (var i = sizes.indexOf(size); i < sizes.length; i++) {
          url = this.attributes.urls[sizes[i]];
          if (url)
            break;
        }

        this.attributes.cache[size] = this.attributes.cache[size] || url;
        this.set('url', this.attributes.cache[size]);
        this.set('preloaded', this.attributes.cache[size]);
      },

      preloadImage: function (size) {
        var model = this;

        var sizes = ['thumb', 'half', 'screen', 'full'];
        var cached;
        for (var i = sizes.indexOf(size); i < sizes.length; i++) {
          cached = cached || this.attributes.cache[sizes[i]];
          if (cached)
            break;
        }

        if (cached) {
          model.set('url', cached);
          model.set('preloaded', size);
          return;
        }

        model.set('preloaded', null);

        var url;
        for (var i = sizes.indexOf(size); i < sizes.length; i++) {
          url = model.attributes.urls[sizes[i]];
          if (url)
            break;
        }

        this.set('loader', $.ajax({
          dataType: 'native',
          url: url,
          xhrFields: {
            responseType: 'blob',
            onprogress: this.xhrProgress,
          }
        }));

        this.attributes.loader.then(function (response) {
          var reader = new FileReader;
          reader.readAsDataURL(response)
          reader.onload = function () {
            // return;
            model.get('cache')[size] = reader.result;
            model.set('url', reader.result);
            model.set('preloaded', size);
            model.set('loader', null);
          };
        });
      }
    }),

    View: Backbone.View.extend({
      initialize: function () {
        var view = this;
        var $img = $('<img></img>').appendTo(this.$el);

        var aspectRatio = this.model.attributes.size.height / this.model.attributes.size.width;
        var spacer = $('<div class="aspect-ratio-spacer"></div>').css({
          'margin-top': aspectRatio * 100 + '%'
        });
        this.$el.append(spacer);
        this.$el.find('img').css({
          'border-bottom-width': aspectRatio * 5 + 'px'
        })
        .toggleClass('aspect-ratio-wide', aspectRatio < 11/8.5);

        view.model.on('change:preloaded', function () {
          view.$el.toggleClass('loading', !view.model.attributes.preloaded);
          view.$el.toggleClass('loaded', !!view.model.attributes.preloaded);
          if (view.model.attributes.preloaded && view.model.attributes.preloaded !== view.model.previous('preloaded'))
            $img.attr('src', view.model.attributes.url);
        });
        view.model.on('change:loader', function () {
          if (view.model.attributes.loader) {
            view.$el.find('.image-label').append($('<div class="loading-indicator">Loading... <span class="progress"></span></div>'));
          } else {
            view.$el.find('.loading-indicator').remove();
          }
        });
        view.model.on('change:visible', function () {
          view.$el.toggleClass('hidden', !view.model.attributes.visible);
        });
        view.model.on('change:percentLoaded', function () {
          view.$el.find('.progress').text(view.model.get('percentLoaded').toFixed(1) + '%');
        });
        view.model.on('change:scale', function () {
          var height = view.model.attributes.size.height * view.model.attributes.scale;
          view.$el.css({
            width: view.model.attributes.size.width * view.model.attributes.scale + 'px',
            height: height + 'px',
            fontSize: view.model.attributes.scale * 32 + 'px'
          });
        });
        view.model.on('change:current', function () {
          view.$el.toggleClass('current', view.model.get('current'));
        });
      }
    }),

    Collection: Backbone.Collection.extend({
      scan: function ($imgs) {
        var coll = this;
        var scrollTop = $imgs.first().closest('.viewport-content').scrollTop();
        $imgs.each(function () {
          var $container = $(this);
          coll.add(new Images.Model({
            $el: $container,
            page: $container.data('page'),
            urls: {
              full: $container.data('screen-url'),
              screen: $container.data('screen-url'),
              // half: $container.data('screen-url'),
              // thumb: $container.data('screen-url'),
              // half: '/static/image_cache/HLSL_NUR_00001001.jpg',
              // thumb: '/static/image_cache/HLSL_NUR_00001001.jpg',
            },
            size: {
              width: parseInt($container.data('width')),
              height: parseInt($container.data('height'))
            },
            screenBounds: {
              top: $container.position().top + scrollTop,
              bottom: $container.position().top + $container.height() + scrollTop,
            },
          }));
        });
        return this;
      },

      resetBounds: function () {
        this.each(function (model) {
          model.attributes.bounds = {
            top: model.attributes.$el.position().top,
            bottom: model.attributes.$el.position().top + model.attributes.$el.height(),
          };
        });
      },
    }),
  };

  return Images;
});
