modulejs.define('DocumentViewport', ['Images', 'DraggingMixin', 'DownloadQueue'], function (Images, DraggingMixin, DownloadQueue) {
  var ImageView = Images.View;
  var ImageModel = Images.Model;
  var ImageCollection = Images.Collection;

  // The view model is just a handy container to track changes to relevant view parameters.
  // All document data is baked in to the HTML template
  var ViewModel = Backbone.Model.extend({
    defaults: {
      scale: 1,
      viewScale: 1,
      maxWidth: 0,
    },

    initialize: function () {
    },
  });

  // This view is the core of the document viewer functionality. It manages everything to do with
  // scrolling, zooming, and navigating pages.
  var View = Backbone.View.extend({
    options: {
      preloadRange: 200,
    },
    initialize: function () {
      var view = this;
      _.bindAll(this, 'zoomIn', 'zoomOut', 'goToPage', 'render', 'setTool', 'smoothZoom', 'wheelZoom', 'magnifyTool', 'toggleExpand', 'recalculateVisible');

      // throttle heavy calls
      this.recalculateVisible = _.debounce(this.recalculateVisible, 50);
      this.smoothZoom = _.throttle(this.smoothZoom, 25);

      // scan all document images into the viewmodel
      var $imgs = this.$el.find('.document-image');
      this.model = new ViewModel({ images: (new ImageCollection).scan($imgs) });
      this.imageViews = _.map(_.zip(this.model.attributes.images.models, $imgs), function (image) {
        return new ImageView({ model: image[0], el: image[1] });
      });

      // stash document data
      this.model.attributes.id = this.$el.data('document-id');
      this.model.attributes.totalPages = this.imageViews.length;

      // set up convenience elements
      this.$viewport = this.$el;
      this.$layout = this.$el.find('.document-image-layout');
      this.pagePlaceholder = $('<div></div>').css({
        display: 'inline-block',
        width: 0,
        height: '1px',
      }).prependTo( this.$layout );

      // set up viewmodel events
      this.model.on({
        'firstVisible': function (firstVisible) {
          // handle a new page scrolling into view
          this.attributes.firstVisible = firstVisible;
          // only change the current page if the old current page is now hidden
          if (!this.attributes.currentImage ||
            this.attributes.currentImage.attributes.$el[0].offsetTop + this.attributes.currentImage.attributes.$el[0].offsetHeight > view.$el.scrollTop() + view.$el.height() ||
            this.attributes.currentImage.attributes.$el[0].offsetTop  < view.$el.scrollTop()
          ) {
            this.set('currentImage', firstVisible);
          }
        },
        'change:currentImage': function () {
          // handle an update to the current image
          var image = view.model.get('currentImage');
          var previous = view.model.previous('currentImage');
          if (!image)
            image = view.model.attributes.currentImage = previous;
          image.set('current', true);
          if (previous)
            previous.set('current', false);

          // don't move to the current page if we already scrolled to it
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

          // broadcast the update
          view.trigger('currentPage', image.attributes.page);
        },
        'change:expand': function () {
          // animate switching to and from the fixed full-screen viewport
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
              view.recalculateVisible();
            })
          } else {
            view.$el.css(this.expandingCSS);
            setTimeout(function () {
              view.$el.removeClass('expanded', view.model.attributes.expand);
              view.$el.removeAttr('style');

              _.defer(view.recalculateVisible);
            }, 300);
          }
        },
        'change:tool': function () {
          // bind events based on tool selection

          // unbind all
          view.$el.removeClass('tool-magnify tool-scroll');
          view.$el.off('mousewheel', view.wheelZoom);
          view.$el.off('click', view.magnifyTool);
          view.$el.off('contextmenu', view.magnifyTool);
          view.$el.off('dblclick', view.magnifyTool);

          if (view.model.attributes.tool === 'magnify') {
            view.$el.addClass('tool-magnify');
            view.$el.on('mousewheel', view.wheelZoom);
            view.$el.on('dblclick', view.magnifyTool);
          } else {
            view.$el.addClass('tool-scroll');
            view.$el.on('click', view.magnifyTool);
            view.$el.on('contextmenu', view.magnifyTool);
          }
        }
      });

      if (!Modernizr.touchevents) {
        this.model.set('tool', 'scroll');
      }

      var stylesheet = document.styleSheets[0];
      var rules = (stylesheet.rules || stylesheet.cssRules);
      if (stylesheet.addRule) {
        stylesheet.addRule("body.document-viewer #document-viewport .document-image",
          "width: 100% !important; height: auto !important;", 0);
      } else if (stylesheet.insertRule) {
        stylesheet.insertRule("body.document-viewer #document-viewport .document-image { width: 100% !important; height: auto !important; }", 0);
      }
      this.imageCSSRule = rules[0];

      this.$el.on('scroll', this.recalculateVisible);
      $(window).on('resize', this.recalculateVisible);
      this.recalculateVisible();
    },

    el: '.viewport-content',

    recalculateVisible: function () {
      // throttled function to test all pages for visibility
      this.testVisible();
    },

    setTool: function (tool) {
      // used by tool buttons
      this.model.set('tool', tool);
    },

    toggleExpand: function (tool) {
      // used to maximize viewport
      this.model.set('expand', !this.model.attributes.expand);
    },

    wheelZoom: function (e) {
      // Event handler for the scroll-to-zoom tool.
      e.preventDefault();
      var scaleOrigin = {x: e.offsetX, y: e.offsetY};
      var scaleDelta = (1 + Math.min(1, Math.max(-1, e.deltaY)) * 0.1);
      var hoveredPage = $(e.target).closest('.document-image');
      this.smoothZoom(this.model.attributes.viewScale * scaleDelta, scaleOrigin);
    },

    magnifyTool: function (e) {
      // Event handler for the default scroll-to-scroll page-zoom tool.
      e.preventDefault();



      var scaleOrigin = {
        x: e.pageX - this.$viewport.offset().left,
        y: e.pageY - this.$viewport.offset().top
      };

      var scale;

      var $page = $(e.target).closest('.document-image');
      var page = _.find(this.imageViews, function (imageView) { return imageView.el === $page[0]; });
      if (page) {
        // select the chosen page
        this.model.attributes.firstVisible = page.model;
        this.model.set('currentImage', page.model);
      }

      // this mode is used in smooth zoom mode to focus on a page. never zooms to page
      if (e.type == 'dblclick') {
        if (this.model.attributes.viewScale >= 1/this.model.attributes.scale) {
          scale = 1;
          this.smoothZoom(scale, scaleOrigin);
        } else {
          this.model.set('viewScale', 1/this.model.attributes.scale);
          this.viewScale(1/this.model.attributes.scale, true, {x: page.$el.position().left, y: page.$el.position().top});
        }
      } else {
        if (!e.which) e.which = e.keyCode;
        if (e.type === 'click' && !e.ctrlKey && !e.metaKey && !e.shiftKey) {
          // on left-click, view scale for 100% and page zoom under 100%
          if (this.model.attributes.scale == 1) {
            scale = 1.5 * this.model.attributes.viewScale;
            this.smoothZoom(scale, scaleOrigin);
          } else {
            scale = 1;
            this.zoomToPage(page, scale);
          }
        } else if (e.type === 'contextmenu' || e.ctrlKey || e.metaKey || e.shiftKey) {
          // on right-click, reset zoom if zoomed in on multiple columns,
          // zoom out if zoomed in on one column, add more columns otherwise
          if (this.model.attributes.viewScale > 1) {
            if (this.model.attributes.scale < 1) {
              scale = 1;
              this.smoothZoom(scale, scaleOrigin);
            } else {
              scale = 1/1.5 * this.model.attributes.viewScale;
              this.smoothZoom(scale, scaleOrigin);
            }
          } else {
            scale = 1/(this.scaleRatio() + 1);
            this.zoomToPage(page, scale);
          }
        }
      }

    },

    smoothZoom: function (viewScale, scaleOrigin) {
      // This is the behavior of the scroll-to-zoom mode. It maintains the number of page columns,
      // and smoothly zooms in and out.

      // Cap view scale.
      // TODO: fix this to be aware of any page scale applied
      this.model.set('viewScale', Math.min(10, Math.max(1, viewScale)));

      if (this.model.attributes.viewScale != this.model.previous('viewScale')) {
        // Calculate the view scale origin necessary to maintain the perceived scale point at the mouse position
        scaleDelta = this.model.attributes.viewScale / this.model.previous('viewScale');
        this.currentOrigin = this.currentOrigin || {
          x: this.$viewport.scrollLeft(),
          y: this.$viewport.scrollTop()
        };
        var targetOrigin = {
          x: Math.max(0, this.currentOrigin.x + scaleOrigin.x - scaleOrigin.x / scaleDelta),
          y: Math.max(0, this.currentOrigin.y + scaleOrigin.y - scaleOrigin.y / scaleDelta),
        };

        // animate the scale change
        this.viewScale(this.model.attributes.viewScale, true, targetOrigin);
      }
    },

    pinnedPageOrigin: function (page) {
      if (!page) {
        return {
          x: this.$viewport.scrollLeft(),
          y: this.$viewport.scrollTop()
        };
      }

      return {
        x: page.$el[0].offsetLeft,
        y: page.$el[0].offsetTop
      };
    },

    zoomToPage: function (page, scale) {
      // This is the behavior of the scroll-mode zoom, which keeps pages fit to the viewport width
      // by adding columns. It works with or without a "target" page to center the zooming on.

      // All animation happens in "view scale", which is complicated, but it stops pages from visibly
      // bouncing around when the number of columns changes.

      var view = this;

      this.model.set('scale', scale);
      var scaleDelta = this.model.attributes.scale / this.model.previous('scale');

      if (scaleDelta < 1) {
        // zoom out

        // Don't let pages become smaller than necessary to fit all in the viewport
        if (this.model.attributes.scale < 1/this.model.attributes.totalPages || $('.document-image-layout').height() <= this.$viewport[0].clientHeight) {
          this.model.attributes.scale = this.model.previous('scale');
          return;
        }

        if (page) {
          // Calculate the offset needed to keep the target page in the same perceived column,
          // and apply that width to the placeholder element.
          var topOffset = Math.max(0, page.$el.position().top - this.$el.scrollTop());
          var oldLanes = this.scaleRatio(this.model.previous('scale'));
          var newLanes = this.scaleRatio();
          var pageIndex = parseInt(page.$el.data('page')) - 1;
          var oldLane = (pageIndex + (this.laneOffset || 0)) % oldLanes;
          var newLane = pageIndex % newLanes;

          // The column is automatically justified to whichever column is closest, minimizing perceived movement.
          if (oldLane >= (newLanes-1)/2) {
            oldLane = newLanes - (newLanes - 1 - oldLane);
          }
          // Only make the offset when necessary to avoid perceived movement.
          if (newLanes > 2 && this.model.attributes.totalPages > 3) {
            this.laneOffset = (oldLane - newLane + newLanes) % newLanes;
            this.pagePlaceholder.css({width: 100 * this.model.attributes.scale * this.laneOffset + '%'});
          }
        } else {
          this.pagePlaceholder.css({width: 0});
        }

        // To zoom out:
        // 1. adjust page scale to new number of lanes
        this.pageScale(this.model.attributes.scale);

        if (page) {
          // If we have a page, attempt to keep its zoom consistent to the side of the viewport it is on
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

        // 2. instantly anti-scale to remove the perceived page scale
        view.viewScale(1/scaleDelta, false, pageOrigin);
        _.defer(function () {
          // 3. animate the view scale to visibly zoom out (next tick, to animate)
          view.viewScale(1, true, {x: 0, y: pageOrigin.y / scaleDelta});
        });
      } else if (scaleDelta > 1) {
        // Zooming in is simpler since we always zoom straight to 100%:
        // 1. animate the view scale in to 100%
        var pageOrigin = this.pinnedPageOrigin(page);
        this.viewScale(scaleDelta, true, pageOrigin);
        this.model.attributes.scaleOrigin = null;
        setTimeout(function () {
          // reset other values for 1 column
          view.pagePlaceholder.css({width: '0%'});
          view.laneOffset = 0;
          view.$viewport.scrollTop(0);
          view.$viewport.scrollLeft(0);
          // 2. instantly remove the view scale
          view.viewScale(1, false, {x: 0, y: 0});
          // 3. replace it with page scale of a single column
          view.pageScale(view.model.attributes.scale);
          if (page) {
            // 4. re-adjust scroll position to keep the zoomed page in view
            view.$viewport.scrollTop(page.$el.position().top);
            view.$viewport.scrollLeft(page.$el.position().left);
          }
        }, 300);
      }


      setTimeout(function () {
        // At the end of a page zoom, we always have no view scaling.
        // Recalculate visible pages after a delay.
        view.model.attributes.viewScale = 1;
        view.recalculateVisible();
      }, 300);
    },

    viewScale: function (scale, animate, scaleOrigin) {
      // View scale is a uniform scaling factor applied to the entire page layout. It is the only
      // animated scaling.

      // TODO: Desynchronized transitions causes visible shaking while scaling. This could be fixed
      // by pre-scaling width, then animating a CSS transform instead.

      var view = this;
      var scaleDelta = scale / (this.prevViewScale || 1);
      this.prevViewScale = scale;
      var duration = 300;

      // scaleOrigin is the layout-space coordinates that will end up at the top-left of the viewport
      // a proper scale origin might be nicer, but this interface is used by more callers
      var transformedOrigin = {
        x: scaleOrigin.x * scaleDelta,
        y: scaleOrigin.y * scaleDelta
      };
      if (animate) {
        // to animate:
        // 0. store the current origin so future smooth zooms don't interrupt this transition
        this.currentOrigin = transformedOrigin;

        // 1. set the target scale and origin offset,
        $('.document-image-layout').css({
          width: 100 * scale + '%',
          left: (- transformedOrigin.x + this.$viewport.scrollLeft()) + 'px',
          top: (- transformedOrigin.y + this.$viewport.scrollTop()) + 'px',
          // add extra margin to avoid forced movement at the layout boundaries before scaling completes
          margin: '0 100% 100% 0',
          transition: animate ? 'width '+duration+'ms, height '+duration+'ms, left '+duration+'ms, top '+duration+'ms' : 'none',
        });

        // only do one transition at a time
        if (this.zoomTimeout) {
          clearTimeout(this.zoomTimeout);
        }
        // 2. wait for transition to complete
        this.zoomTimeout = setTimeout(function () {
          // clear the current animation
          view.zoomTimeout = null;
          view.currentOrigin = null;

          // reset the origin offset, and apply it as a scroll offset instead
          $('.document-image-layout').css({
            left: 0,
            top: 0,
            margin: 0,
            // add extra margin needed to avoid a jump when switching to scroll offset
            'margin-bottom': Math.max(0, (transformedOrigin.y + view.$viewport[0].clientHeight) - $('.document-image-layout').height()) + 'px',
            transition: 'none',
          });
          view.$viewport.scrollLeft(transformedOrigin.x);
          view.$viewport.scrollTop(transformedOrigin.y);

          // recalculate visible pages with the new scroll coordinates
          view.recalculateVisible();
        }, duration);
      } else {
        // if not animating, this is a call to pre-set the scale and origin for a future transition
        $('.document-image-layout').css({
          width: 100 * scale + '%',
          left: (- transformedOrigin.x + this.$viewport.scrollLeft()) + 'px',
          top: (- transformedOrigin.y + this.$viewport.scrollTop()) + 'px',
          transition: 'none',
        });
      }
    },
    pageScale: function (scale) {
      // Page scale controls the number of visible page columns, and is never animated.
      var $viewport = $('.viewport-content');

      // apply individual scale as a CSS rule rather than to each page individually
      if (this.imageCSSRule) {
        // TODO: font-size is not animated properly during view scaling...
        var fn = this.imageCSSRule.style.setAttribute ? 'setAttribute' : 'setProperty';
        this.imageCSSRule.style[fn]('font-size', 48 * scale + 'px', 'important');
        this.imageCSSRule.style[fn]('line-height', 64 * scale + 'px', 'important');
        this.imageCSSRule.style[fn]('height', 'auto', 'important');
        this.imageCSSRule.style[fn]('width', 100 * scale + '%', 'important');
      }
    },

    scaleRatio: function (scale) {
      // return the current or provided scale as a number of visible columns
      scale = scale || this.model.attributes.scale;
      return Math.min(10, Math.max(1, Math.floor(1/scale)));
    },

    zoomIn: function () {
      // behavior of the "zoom in" button
      // Page zoom over 100%, smooth zoom under 100%
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
      // behavior of the "zoom out" button
      // Page zoom over 100%, smooth zoom under 100%
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
      // bring the provided page number into view, used by page selection tools
      var image = this.model.attributes.images.find(function (i) { return i.attributes.page == page; });
      if (image) {
        this.model.attributes.firstVisible = null;
        this.model.set('currentImage', image);
      }
    },

    preloadRange: function (fromPage, toPage) {
      // force preloading of the specified page numbers, and return a promise providing load progress
      // used by PDF generation

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

    findVisible: function (first, last, bounds) {
      // binary search to find any visible page, minimizes dom reads
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
      // Scan all image views, marking which ones are currently visible in the viewport for preloading

      var model = this.model;
      DownloadQueue.resetPriority();

      var $parent = this.$el;
      if (Modernizr.touchevents) {
        $parent = $(window);
      }

      // cache viewport bounds
      var bounds = {
        top: $parent.scrollTop(),
        left: $parent.scrollLeft()
      }
      bounds.right = bounds.left + $parent.width();
      bounds.bottom = bounds.top + $parent.height();

      // to preload pages within a certain distance of visible
      bounds.top -= this.options.preloadRange;
      bounds.bottom += this.options.preloadRange;

      // find any visible page
      // TODO: It might save time to start looking in the currently visible page, or to do
      // a second binary search for the viewable edges
      var visibleIndex = this.findVisible(0, this.imageViews.length - 1, bounds);

      var firstVisible = visibleIndex, lastVisible = visibleIndex;

      // look back for the first visible page
      for (var i = visibleIndex - 1; i >= 0; i--) {
        if (!this.isVisible(i, bounds))
          break;
        firstVisible = i;
      }

      // look forward for the last visible page
      for (var i = visibleIndex + 1; i < this.model.attributes.totalPages; i++) {
        if (!this.isVisible(i, bounds))
          break;
        lastVisible = i;
      }

      // after finding the visible range, set all models visible in a batch to separate from the
      // DOM reads
      this.model.attributes.images.each(function (image, n) {
        if (n >= firstVisible && n <= lastVisible) {
          image.set('scale', model.attributes.scale * model.attributes.viewScale);
          image.set('visible', true);
        } else {
          image.set('visible', false);
        }
      });

      if (firstVisible !== null) {
        // test to find the first page that is truly visible, not in preload range
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
