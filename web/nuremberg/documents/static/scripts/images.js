modulejs.define('Images', ['DownloadQueue'], function (DownloadQueue) {
  // the image view and model are encapsulate functionality specific to a single page,
  // mainly pre-loading and rendering the appropriate URL when page visibliity changes
  var Images = {
    Model: Backbone.Model.extend({
      defaults: {
        scale: 1,
        visible: false,
        preloaded: false,
        loader: null
      },
      initialize: function () {
        _.bindAll(this, 'handleVisible', 'downloadProgress');

        this.on({
          'change:visible': this.handleVisible,
          'change:scale': this.handleVisible
        });
        this.attributes.cache = {};
      },

      downloadProgress: function (e) {
        this.set('percentLoaded', (e.loaded / (e.total || 150 * 1024)) * 100);
      },

      handleVisible: function () {
        var model = this;
        _.defer(function () {
          if (model.get('visible')) {
            var scale = model.attributes.scale;
            if (model.attributes.$el.width() > model.attributes.size.width || scale > 2) {
              model.preloadImage('full');
            } else if (model.attributes.$el.width() < 250) {
              model.preloadImage('thumb');
            } else {
              model.preloadImage('screen');
            }
          } else {
            if (model.attributes.loader) {
              // aborting is handled by queue now
              // model.attributes.loader.abort();
              // model.set('loader', null);
            }
          }
        });
      },

      preloadImage: function (size) {
        if (this.attributes.loader) {
          if (this.attributes.loader.size == size) {
            DownloadQueue.refresh(this.attributes.loader);
            return;
          } else {
            this.attributes.loader.cancel();
          }
        }

        var model = this;

        var sizes = ['thumb', 'screen', 'full', 'screen', 'thumb'];
        var url;
        for (var i = sizes.indexOf(size); i < sizes.length; i++) {
          size = sizes[i];
          url = model.attributes.urls[size];
          if (url)
          break;
        }

        sizes = ['thumb', 'screen', 'full'];
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


        this.set('loader', DownloadQueue.download(url, this.attributes.img));


        this.attributes.loader.size = size;
        this.attributes.loader
        .progress(this.downloadProgress)
        .then(function (response) {
          if (response === 'fallback') {
            // the img tag is already loaded
            model.get('cache')[size] = model.attributes.img.src;
            model.set('url', model.attributes.img.src);
            model.set('preloaded', size);
            model.set('loader', null);
          } else {
            var reader = new FileReader;
            reader.readAsDataURL(response)
            reader.onload = function () {
              model.get('cache')[size] = reader.result;
              model.set('url', reader.result);
              model.set('preloaded', size);
              model.set('loader', null);
            };
          }
        })
        .fail(function (error) {
          model.set('loader', null);
        });
      }
    }),

    View: Backbone.View.extend({
      initialize: function () {
        var view = this;
        var $img = $('<img></img>').appendTo(this.$el);
        this.model.attributes.img = $img[0];

        var aspectRatio = this.model.attributes.size.height / this.model.attributes.size.width;
        var spacer = $('<div class="aspect-ratio-spacer"></div>').css({
          'margin-top': aspectRatio * 100 + '%'
        });
        this.$el.append(spacer);
        this.$el.find('img').css({
          'border-bottom-width': aspectRatio * 5 + 'px'
        })
        .toggleClass('aspect-ratio-wide', aspectRatio < 11/8.5)
        .attr('alt', this.model.attributes.alt);

        view.model.on('change:preloaded', function () {
          view.$el.toggleClass('rendered-thumb', !view.model.attributes.preloaded && view.model.previous('preloaded') == 'thumb');
          view.$el.toggleClass('loading', !view.model.attributes.preloaded);
          view.$el.toggleClass('loaded', !!view.model.attributes.preloaded);
          if (view.model.attributes.preloaded && view.model.attributes.preloaded !== view.model.previous('preloaded'))
            $img.attr('src', view.model.attributes.url);
        });
        view.model.on('change:loader', function () {
          if (view.model.attributes.loader) {
            if (!view.$el.find('.image-label .loading-indicator').length)
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

        if (!Modernizr.touchevents) {
          // queue up all thumbnails, if nothing else is going on
          this.model.preloadImage('thumb');
        }
      }
    }),

    Collection: Backbone.Collection.extend({
      scan: function ($imgs) {
        var coll = this;
        var scrollTop = $imgs.first().closest('.viewport-content').scrollTop();
        $imgs.each(function () {
          var $container = $(this);
          coll.add(new Images.Model({
            el: this,
            $el: $container,
            page: $container.data('page'),
            alt: $container.data('alt'),
            urls: {
              full: $container.data('full-url'),
              screen: $container.data('screen-url'),
              thumb: $container.data('thumb-url'),
            },
            size: {
              width: parseInt($container.data('width')),
              height: parseInt($container.data('height'))
            },
          }));
        });
        return this;
      },
    }),
  };

  return Images;
});
