modulejs.define('DocumentViewport', ['Images', 'DraggingMixin', 'DownloadQueue'], function (Images, DraggingMixin, DownloadQueue) {
  var ImageView = Images.View;
  var ImageModel = Images.Model;
  var ImageCollection = Images.Collection;

  var ViewModel = Backbone.Model.extend({
    defaults: {
      scale: 1,
      viewScale: 1,
      maxWidth: 0,
    },

    initialize: function () {
    },
  });

  var View = Backbone.View.extend({
    options: {
      preloadRange: 200,
    },
    initialize: function () {
      var view = this;
      this.recalculateVisible = _.debounce(this.recalculateVisible, 50);
      _.bindAll(this, 'zoomIn', 'zoomOut', 'goToPage', 'render', 'setTool', 'smoothZoom', 'wheelZoom', 'pageZoom', 'toggleExpand', 'recalculateVisible');

      this.smoothZoom = _.throttle(this.smoothZoom, 25);


      var $imgs = this.$el.find('.document-image');
      this.model = new ViewModel({ images: (new ImageCollection).scan($imgs) });

      this.imageViews = _.map(_.zip(this.model.attributes.images.models, $imgs), function (image) {
        return new ImageView({ model: image[0], el: image[1] });
      });

      this.model.attributes.id = this.$el.data('document-id');
      this.model.attributes.totalPages = this.imageViews.length;

      this.pagePlaceholder = $('<div></div>').css({
        display: 'inline-block',
        width: 0,
        height: '10px',
      });
      this.$el.find('.document-image-layout').prepend(this.pagePlaceholder);

      var $viewport = $('.viewport-content');
      this.imageViews.forEach(function (imageView) {
        imageView.on('zoom', function () {
          if (view.model.attributes.scale == 1) {
            view.zoomToPage(imageView, 1/4)
          } else {
            view.zoomToPage(imageView, 1);
          }
        });
      });

      this.model.on({
        'firstVisible': function (firstVisible) {
          this.attributes.firstVisible = firstVisible;
          console.log('first visible', firstVisible.attributes.page)
          if (!this.attributes.currentImage ||
            this.attributes.currentImage.attributes.$el[0].offsetTop + this.attributes.currentImage.attributes.$el[0].offsetHeight > view.$el.scrollTop() + view.$el.height() ||
            this.attributes.currentImage.attributes.$el[0].offsetTop  < view.$el.scrollTop()
          ) {
            this.set('currentImage', firstVisible);
          }
        },
        'change:currentImage': function () {
          var image = view.model.get('currentImage');
          var previous = view.model.previous('currentImage');
          if (!image)
            image = view.model.attributes.currentImage = previous;
          image.set('current', true);
          if (previous)
            previous.set('current', false);
          console.log('current image', image.attributes.page)

          if (image !== view.model.attributes.firstVisible) {
            if (Modernizr.touchevents) {
              $(window).scrollTop(image.attributes.el.offsetTop);
            } else {
              if (view.$el.scrollTop() > image.attributes.el.offsetTop || view.$el.scrollTop() + view.$el.height() < image.attributes.el.offsetTop + image.attributes.el.offsetHeight)
              view.$el.scrollTop(image.attributes.el.offsetTop);
              if (view.$el.scrollLeft() > image.attributes.el.offsetLeft || view.$el.scrollLeft() + view.$el.width() < image.attributes.el.offsetLeft + image.attributes.el.offsetWidth)
              view.$el.scrollLeft(image.attributes.el.offsetLeft);
            }
          }

          view.trigger('currentPage', image.attributes.page);
        },
        'change:expand': function () {
          if (view.model.attributes.expand) {
            var rect = view.el.getBoundingClientRect();
            this.expandingCSS = {
              position: 'fixed',
              left: Math.max(0, rect.left),
              top: Math.max(0, rect.top),
              right: $(window).width() - Math.max(0, rect.right),
              bottom: $(window).height() - Math.max(0, rect.bottom),
              'border-width': 0,
              'border-top-width': 0,
              'background-color': 'transparent',
            };
            view.$el.css(this.expandingCSS);
            view.$el.addClass('expanded');
            _.defer(function () {
              view.$el.removeAttr('style');
              _.defer(view.recalculateVisible());
            })
          } else {
            view.$el.css(this.expandingCSS);
            setTimeout(function () {
              view.$el.removeClass('expanded', view.model.attributes.expand);
              view.$el.removeAttr('style');

              _.defer(view.recalculateVisible());
            }, 300);
          }
        },
        'change:tool': function () {
          view.$el.removeClass('tool-magnify tool-scroll');
          view.$el.off('mousewheel', view.wheelZoom);
          view.$el.off('click', view.pageZoom);
          view.$el.off('contextmenu', view.pageZoom);
          view.$el.off('dblclick', view.pageZoom);
          if (view.model.attributes.tool === 'magnify') {
            view.$el.addClass('tool-magnify');
            view.$el.on('mousewheel', view.wheelZoom);
            view.$el.on('dblclick', view.pageZoom);
          } else {
            view.$el.addClass('tool-scroll');
            view.$el.on('click', view.pageZoom);
            view.$el.on('contextmenu', view.pageZoom);
          }
        }
      });

      if (!Modernizr.touchevents) {
        this.model.set('tool', 'scroll');
      }

      this.imageCSSRule = document.styleSheets[0].cssRules[
        document.styleSheets[0].insertRule("body.document-viewer #document-viewport .document-image { width: 100% !important; height: auto !important; }", 0)
      ];

      this.$el.on('scroll', this.recalculateVisible);
      $(window).on('resize', this.recalculateVisible);
      this.recalculateVisible();
    },

    el: '.viewport-content',

    recalculateVisible: function () {
      this.testVisible();
    },

    setTool: function (tool) {
      this.model.set('tool', tool);
    },

    toggleExpand: function (tool) {
      this.model.set('expand', !this.model.attributes.expand);
    },

    wheelZoom: function (e) {
      e.preventDefault();
      var scaleOrigin = {x: e.offsetX, y: e.offsetY};
      var scaleDelta = (1 + Math.min(1, Math.max(-1, e.deltaY)) * 0.1);
      var hoveredPage = $(e.target).closest('.document-image');
      this.smoothZoom(this.model.attributes.viewScale * scaleDelta, scaleOrigin, hoveredPage);
    },

    pageZoom: function (e) {
      e.preventDefault();
      var $viewport = $('.viewport-content');

      var scaleOrigin = {
        x: e.pageX - $viewport.offset().left,
        y: e.pageY - $viewport.offset().top
      };

      var scale;

      var $page = $(e.target).closest('.document-image');
      var page = _.find(this.imageViews, function (imageView) { return imageView.el === $page[0]; });
      if (page) {
        this.model.attributes.firstVisible = page.model;
        this.model.set('currentImage', page.model);
      }

      if (e.type == 'dblclick') {
        if (this.model.attributes.viewScale >= 1/this.model.attributes.scale) {
          scale = 1;
          this.smoothZoom(scale, scaleOrigin, page);
        } else {
          this.model.set('viewScale', 1/this.model.attributes.scale);
          this.viewScale(1/this.model.attributes.scale, true, {x: page.$el.position().left, y: page.$el.position().top});
        }
      } else {
        if (e.which === 1) {
          if (this.model.attributes.scale == 1) {
            scale = 1.5 * this.model.attributes.viewScale;
            this.smoothZoom(scale, scaleOrigin, page);
          } else {
            scale = 1;
            this.zoomToPage(page, scale);
          }
        } else if (e.which === 3) {
          if (this.model.attributes.viewScale > 1) {
            if (this.model.attributes.scale < 1) {
              scale = 1;
              this.smoothZoom(scale, scaleOrigin, page);
            } else {
              scale = 1/1.5 * this.model.attributes.viewScale;
              this.smoothZoom(scale, scaleOrigin, page);
            }
          } else {
            scale = 1/(this.scaleRatio() + 1);
            this.zoomToPage(page, scale);
          }
        } else {
          return;
        }
      }

    },

    smoothZoom: function (viewScale, scaleOrigin, pinnedPage) {
      var $viewport = $('.viewport-content');

      this.model.set('viewScale', Math.min(10, Math.max(1, viewScale)));

      if (this.model.attributes.viewScale != this.model.previous('viewScale')) {
        scaleDelta = this.model.attributes.viewScale / this.model.previous('viewScale');
        this.currentOrigin = this.currentOrigin || {
          x: $viewport.scrollLeft(),
          y: $viewport.scrollTop()
        };
        var targetOrigin = {
          x: Math.max(0, this.currentOrigin.x + scaleOrigin.x - scaleOrigin.x / scaleDelta),
          y: Math.max(0, this.currentOrigin.y + scaleOrigin.y - scaleOrigin.y / scaleDelta),
        };
        this.viewScale(this.model.attributes.viewScale, true, targetOrigin);
      }
    },

    pinnedPageOrigin: function (page) {
      if (!page)
        return;

      return {
        x: page.$el[0].offsetLeft,
        y: page.$el[0].offsetTop
      };
    },

    zoomToPage: function (page, scale) {
      var $viewport = $('.viewport-content');
      var view = this;

      this.model.set('scale', scale);
      var scaleDelta = this.model.attributes.scale / this.model.previous('scale');

      if (scaleDelta < 1) {
        // zoom out
        if (this.model.attributes.scale < 1/this.model.attributes.totalPages || $('.document-image-layout').height() <= $viewport[0].clientHeight) {
          this.model.attributes.scale = this.model.previous('scale');
          return;
        }

        if (page) {
          var topOffset = Math.max(0, page.$el.position().top - this.$el.scrollTop());
          var oldLanes = this.scaleRatio(this.model.previous('scale'));
          var newLanes = this.scaleRatio();
          var pageIndex = parseInt(page.$el.data('page')) - 1;
          var oldLane = (pageIndex + (this.laneOffset || 0)) % oldLanes;
          var newLane = pageIndex % newLanes;
          if (oldLane >= (newLanes-1)/2) {
            oldLane = newLanes - (newLanes - 1 - oldLane);
          }
          if (newLanes > 2 && this.model.attributes.totalPages > 3) {
            this.laneOffset = (oldLane - newLane + newLanes) % newLanes;
            this.pagePlaceholder.css({width: 100 * this.model.attributes.scale * this.laneOffset + '%'});
          }
        } else {
          this.laneOffset = (oldLane - newLane + newLanes) % newLanes;
          this.pagePlaceholder.css({width: 0});
        }
        this.pageScale(this.model.attributes.scale);
        if (page) {
          var pageOrigin = view.pinnedPageOrigin(page);
          if (oldLane >= (newLanes-1)/2 || newLanes == 2 && newLane == 1) {
            pageOrigin.x = this.$el.width() - this.$el.width() * scaleDelta;
          } else if (page) {
            pageOrigin.x = 0;
          }
          pageOrigin.y -= topOffset * scaleDelta;
        } else {
          pageOrigin = {x: 0, y: 0};
        }
        view.viewScale(1/scaleDelta, false, pageOrigin);
        _.defer(function () {
          view.viewScale(1, true, {x: 0, y: pageOrigin.y / scaleDelta});
        });
      } else if (scaleDelta > 1) {
        // zoom in
        var pageOrigin = this.pinnedPageOrigin(page);
        this.viewScale(scaleDelta, true, pageOrigin);
        this.model.attributes.scaleOrigin = null;
        setTimeout(function () {
          view.pagePlaceholder.css({width: '0%'});
          view.laneOffset = 0;
          $viewport.scrollTop(0);
          $viewport.scrollLeft(0);
          view.viewScale(1, false, {x: 0, y: 0});
          view.pageScale(view.model.attributes.scale);
          if (page) {
            $viewport.scrollTop(page.$el.position().top);
            $viewport.scrollLeft(page.$el.position().left);
          }
        }, 300);
      }

      setTimeout(function () {
        view.model.attributes.viewScale = 1;
        view.model.attributes.skipTest = false;
        view.recalculateVisible();
      }, 300);
    },
    viewScale: function (scale, animate, scaleOrigin) {
      var view = this;
      var scaleDelta = scale / (this.prevViewScale || 1);
      this.prevViewScale = scale;

      var $viewport = $('.viewport-content');
      var duration = 300;
      if (!scaleOrigin) {
        if (scale >= 1) {
          scaleOrigin = {
            x: $viewport.scrollLeft(),
            y: $viewport.scrollTop()
          };
        } else {
          scaleOrigin = {
            x: 0,
            y: 0,
          };
        }
      }
      var transformedOrigin = {
        x: scaleOrigin.x * scaleDelta,
        y: scaleOrigin.y * scaleDelta
      };
      if (animate) {
        this.currentOrigin = transformedOrigin;
        $('.document-image-layout').css({
          width: 100 * scale + '%',
          left: (- transformedOrigin.x + $viewport.scrollLeft()) + 'px',
          top: (- transformedOrigin.y + $viewport.scrollTop()) + 'px',
          // 'margin-bottom': Math.max(0, (transformedOrigin.y + $viewport[0].clientHeight * scaleDelta) - $('.document-image-layout').height()) + 'px',
          margin: '0 100% 100% 0',
          transition: animate ? 'width '+duration+'ms, height '+duration+'ms, left '+duration+'ms, top '+duration+'ms' : 'none',
        });
        if (this.zoomTimeout) {
          clearTimeout(this.zoomTimeout);
        }
        this.zoomTimeout = setTimeout(function () {
          view.zoomTimeout = null;
          view.currentOrigin = null;
          $('.document-image-layout').css({
            left: 0,
            top: 0,
            margin: 0,
            'margin-bottom': Math.max(0, (transformedOrigin.y + $viewport[0].clientHeight) - $('.document-image-layout').height()) + 'px',
            transition: 'none',

          });
          $viewport.scrollLeft(transformedOrigin.x);
          $viewport.scrollTop(transformedOrigin.y);
          view.recalculateVisible();
        }, duration);
      } else {
        $('.document-image-layout').css({
          width: 100 * scale + '%',
          left: (- transformedOrigin.x + $viewport.scrollLeft()) + 'px',
          top: (- transformedOrigin.y + $viewport.scrollTop()) + 'px',
          transition: 'none',
        });
      }
    },
    pageScale: function (scale) {
      var $viewport = $('.viewport-content');

      if (this.imageCSSRule) {
        this.imageCSSRule.style.setProperty('font-size', 48 * scale + 'px', 'important');
        this.imageCSSRule.style.setProperty('line-height', 64 * scale + 'px', 'important');
        this.imageCSSRule.style.setProperty('height', 'auto', 'important');
        this.imageCSSRule.style.setProperty('width', 100 * scale + '%', 'important');
        // this.imageCSSRule.style.setProperty('border-width', 25 * scale + 'px', 'important');

        if (this.scaleRatio() != this.renderedScaleRatio) {
          // this.layoutImages();
          this.renderedScaleRatio = this.scaleRatio();
        }
      }
    },

    layoutImages: function () {
      var view = this;
      var top = 0, maxWidth = 0;
      var lanes = this.scaleRatio();
      var lane = 1, row = 1;
      this.imageViews.forEach(function (imageView, n) {
        var myLane = lane;
        var myTop = top;
        setTimeout(function () {
          imageView.$el.css({
            position: 'absolute',
            left: 100/lanes * (myLane - 1) + '%',
            top: myTop + 'px',
          });
        }, 50 * row);
        lane += 1;
        if (lane > lanes) {
          row += 1;
          lane = 1;
          top += imageView.model.attributes.size.height * view.model.attributes.scale + 10;
        }
        maxWidth = Math.max(maxWidth, imageView.model.attributes.size.width);
      });
    },

    scaleRatio: function (scale) {
      scale = scale || this.model.attributes.scale;
      return Math.min(10, Math.max(1, Math.floor(1/scale)));
    },
    zoomIn: function () {
      var scale = this.model.attributes.scale * this.model.attributes.viewScale;
      if (scale < 1) {
        var firstVisible = this.model.attributes.firstVisible;
        scale = 1/(this.scaleRatio(scale) - 1);
        this.zoomToPage(_.find(this.imageViews, function (view) {return view.model === firstVisible}), scale);
      } else {
        scale = 1.5 * this.model.attributes.viewScale;
        this.smoothZoom(scale, {x: this.$el.width()/2, y: this.$el.height()/2});
      }
    },
    zoomOut: function () {
      var scale = this.model.attributes.scale * this.model.attributes.viewScale;
      if (scale <= 1) {
        var firstVisible = this.model.attributes.firstVisible;
        scale = 1/Math.min(10, this.scaleRatio(scale) + 1);
        this.zoomToPage(_.find(this.imageViews, function (view) {return view.model === firstVisible}), scale);
      } else {
        scale = 1/1.5 * this.model.attributes.viewScale;
        this.smoothZoom(scale, {x: this.$el.width()/2, y: this.$el.height()/2});
      }
    },
    goToPage: function (page) {
      var image = this.model.attributes.images.find(function (i) { return i.attributes.page == page; });
      if (image) {
        this.model.attributes.firstVisible = null;
        this.model.set('currentImage', image);
      }
    },

    hardloadAll: function (size) {
      var view = this;
      size = size || 'screen';
      this.model.attributes.images.each(function (image) {
        image.hardload(size);
      });
    },

    preloadRange: function (fromPage, toPage) {
      var view = this;
      var size = size || 'screen';
      var promise = $.Deferred()
      fromPage -= 1;
      toPage -= 1;
      var total = toPage - fromPage + 1;
      var loaded = 0;
      var complete = function () {
        promise.notify();
        loaded += 1;
        if (loaded == total) {
          promise.resolve();
        }
      };
      this.model.attributes.images.each(function (image, n) {
        if (n >= fromPage && n <= toPage) {
          image.preloadImage(size);
          if (image.attributes.preloaded) {
            complete();
          } else {
            image.once('change:preloaded', complete);
          }
        }
      });
      return promise;
    },

    zoomToFit: function () {
      this.pageScale(1);
    },



    findVisible: function (first, last, bounds) {
      // binary search to find any visible page
      if (first > last)
        return null;

      var midpoint = Math.floor((last + first) / 2);
      var testPage = this.imageViews[midpoint];

      var testBounds = {
        left: testPage.el.offsetLeft,
        top: testPage.el.offsetTop,
      }
      testBounds.bottom = testBounds.top + testPage.el.offsetHeight;
      testBounds.right = testBounds.left + testPage.el.offsetWidth;

      if (bounds.top > testBounds.bottom) {
        // too high, search after midpoint
        return this.findVisible(midpoint + 1, last, bounds);
      } else if (bounds.bottom < testBounds.top) {
        // too low, search before midpoint
        return this.findVisible(first, midpoint - 1, bounds)
      } else {
        // to make scanning logic simpler, just load whole rows
        //
        // if (bounds.right < testBounds.left) {
        //   // too left, search after midpoint
        //   return this.findVisible(midpoint + 1, last, bounds);
        // } else if (bounds.left > testBounds.right) {
        //   // too right, search before midpoint
        //   return this.findVisible(first, midpoint - 1, bounds)
        // } else {
          // overlapping, this is visible
          return midpoint;
        // }
      }
    },

    isVisible: function (n, bounds) {
      return this.findVisible(n, n, bounds) !== null;
    },

    testVisible: function () {
      var model = this.model;
      if (this.model.attributes.skipTest)
        return;

      DownloadQueue.resetPriority();

      var $parent = this.$el;
      if (Modernizr.touchevents) {
        $parent = $(window);
      }

      var bounds = {
        top: $parent.scrollTop(),
        left: $parent.scrollLeft()
      }
      bounds.right = bounds.left + $parent.width();
      bounds.bottom = bounds.top + $parent.height();

      bounds.top -= this.options.preloadRange;
      bounds.bottom += this.options.preloadRange;

      var visibleIndex = this.findVisible(0, this.imageViews.length - 1, bounds);

      var firstVisible = visibleIndex, lastVisible = visibleIndex;

      for (var i = visibleIndex - 1; i >= 0; i--) {
        if (!this.isVisible(i, bounds))
          break;
        firstVisible = i;
      }
      for (var i = visibleIndex + 1; i < this.model.attributes.totalPages; i++) {
        if (!this.isVisible(i, bounds))
          break;
        lastVisible = i;
      }

      var model = this.model;

      this.model.attributes.images.each(function (image, n) {
        if (n >= firstVisible && n <= lastVisible) {
          image.set('scale', model.attributes.scale * model.attributes.viewScale);
          image.set('visible', true);
        } else {
          image.set('visible', false);
        }
      });
      if (firstVisible !== null) {
        var testPage = this.imageViews[firstVisible];
        bounds.top += this.options.preloadRange;
        bounds.bottom -= this.options.preloadRange;
        var testBounds = {
          top: testPage.el.offsetTop,
        }
        testBounds.bottom = testBounds.top = testBounds.top + testPage.el.offsetHeight / 2;
        if (testBounds.top > bounds.bottom) {
          firstVisible = Math.max(0, firstVisible - this.scaleRatio());
        } else if (testBounds.bottom < bounds.top) {
          firstVisible = Math.min(this.model.attributes.totalPages - 1, firstVisible + this.scaleRatio());
        }
        this.model.trigger('firstVisible', this.imageViews[firstVisible].model);
      }
    },
  });

  DraggingMixin.mixin(View);

  return View;
});
