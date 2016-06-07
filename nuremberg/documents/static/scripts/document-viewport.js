modulejs.define('DocumentViewport', ['Images', 'DraggingMixin'], function (Images, DraggingMixin) {
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
      this.on({
        'change:bounds': this.testVisible,
        // 'change:scale': this.scaleImages,
      });
    },

    testVisible: function () {
      if (this.attributes.skipTest)
        return;

      var model = this;
      var bounds = this.get('bounds');

      var firstVisible;
      this.attributes.images.each(function (image) {
        var imageBounds = image.attributes.bounds;
        // console.log('testing image', imageBounds.top, imageBounds.bottom, 'scroll', bounds.top, bounds.bottom, 'pass', imageBounds.top < bounds.bottom, imageBounds.bottom > bounds.top);
        image.attributes.scale = model.attributes.scale;
        image.set('visible', imageBounds.top - bounds.bottom < 1000 && imageBounds.bottom - bounds.top > -1000);
        if (!firstVisible && bounds.top <= Math.max(imageBounds.bottom - 60, 0)) {
          firstVisible = image;
        }
      });
      if (firstVisible)
        this.trigger('firstVisible', firstVisible);
    },

    scaleImages: function () {
      var model = this;
      var scale = this.get('scale');

      this.attributes.images.each(function (image) {
        image.set('scale', scale);
        image.attributes.visible = false;
      });

      var scrollHeight = $('.viewport-content')[0].scrollHeight;
      var scrollTop = $('.viewport-content').scrollTop() + $('.viewport-content').height()/2;
      setTimeout(function () {
        model.attributes.images.resetBounds();
        $('.viewport-content').scrollTop((scrollTop / scrollHeight) * $('.viewport-content')[0].scrollHeight - $('.viewport-content').height()/2);
      }, 300);
    },
  });

  var View = Backbone.View.extend({
    initialize: function () {
      var view = this;
      _.bindAll(this, 'setBounds', 'zoomIn', 'zoomOut', 'goToPage', 'render', 'setTool', 'smoothZoom', 'wheelZoom', 'pageZoom', 'toggleExpand');

      this.smoothZoom = _.throttle(this.smoothZoom, 25);

      var $imgs = this.$el.find('.document-image');
      this.model = new ViewModel({ images: (new ImageCollection).scan($imgs) });

      this.imageViews = _.map(_.zip(this.model.attributes.images.models, $imgs), function (image) {
        return new ImageView({ model: image[0], el: image[1] });
      });

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
          if (!this.attributes.currentImage || (this.attributes.currentImage.attributes.bounds.bottom > view.$el.scrollTop() + view.$el.height() || this.attributes.currentImage.attributes.bounds.top  < view.$el.scrollTop()))
            this.set('currentImage', firstVisible);
        },
        'change:currentImage': function () {
          var image = view.model.get('currentImage');
          var previous = view.model.previous('currentImage');
          if (!image)
            image = view.model.attributes.currentImage = previous;
          image.set('current', true);
          if (previous)
            previous.set('current', false);

          if (image !== view.model.attributes.firstVisible) {
            if (view.$el.scrollTop() > image.attributes.bounds.top || view.$el.scrollTop() + view.$el.height() < image.attributes.bounds.bottom)
              view.$el.scrollTop(image.attributes.bounds.top);
            if (view.$el.scrollLeft() > image.attributes.$el.position().left || view.$el.scrollLeft() + view.$el.width() < image.attributes.$el.position().left + image.attributes.$el.width())
              view.$el.scrollLeft(image.attributes.$el.position().left);
          }

          view.trigger('currentPage', image.attributes.page);
        },
        'change:expand': function () {
          if (view.model.attributes.expand) {
            this.expandingCSS = {
              position: 'fixed',
              left: view.$el.offset().left+'px',
              top: view.$el.offset().top+'px',
              right: $(window).width() - (view.$el.offset().left + view.$el.width())+'px',
              bottom: Math.max(0, $(window).height() - (view.$el.offset().top + view.$el.height()))+'px',
              'border-width': 0,
            };
            view.$el.css(this.expandingCSS);
            view.$el.addClass('expanded');
            _.defer(function () {
              view.$el.removeAttr('style');
              _.defer(function () {
                view.model.attributes.images.resetBounds();
                view.setBounds();
              });
            })
          } else {
            view.$el.css(this.expandingCSS);
            setTimeout(function () {
              view.$el.removeClass('expanded', view.model.attributes.expand);
              view.$el.removeAttr('style');

              _.defer(function () {
                view.model.attributes.images.resetBounds();
                view.setBounds();
              });
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

      this.model.set('tool', 'scroll');

      this.imageCSSRule = document.styleSheets[0].cssRules[
        document.styleSheets[0].insertRule("body.document-viewer #document-viewport .document-image { width: 100% !important; height: auto !important; }", 0)
      ];

      $(window).on('resize', this.setBounds);
      this.model.attributes.images.resetBounds();
      this.setBounds();
    },

    el: '.viewport-content',

    events: {
      'scroll': 'setBounds',
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
          var scaleDelta = 1/this.model.attributes.viewScale;
          var scaleOrigin = {
            x: $viewport.scrollLeft(),
            y: $viewport.scrollTop()
          };
          this.viewScale(this.model.attributes.viewScale, false, scaleOrigin);
          this.model.set('viewScale', 1);
          this.viewScale(1, true, scaleOrigin);
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
            scale = 1/1.5 * this.model.attributes.viewScale;
            this.smoothZoom(scale, scaleOrigin, page);
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

      this.model.set('viewScale', Math.min(10, Math.max(0.25, viewScale)));

      if (this.model.attributes.viewScale != this.model.previous('viewScale')) {
        if (this.model.attributes.viewScale < 1) {
          // var totalScaleRatio = this.scaleRatio(this.model.attributes.viewScale * this.model.attributes.scale);
          // if (totalScaleRatio < 5) {
          //   this.model.attributes.scale = 1/(totalScaleRatio + 1);
          //   this.model.attributes.viewScale = 1/(totalScaleRatio * this.model.attributes.scale);
          //   if (pinnedPage && pinnedPage.length) {
          //     var hoveredOffset = {
          //       x: $viewport.scrollTop() - pinnedPage.position().top,
          //       y: $viewport.scrollLeft() - pinnedPage.position().left,
          //     };
          //   }
          //
          //   this.pageScale(this.model.attributes.scale);
          //   this.viewScale(this.model.attributes.viewScale, false);
          //   if (hoveredOffset) {
          //     $viewport.scrollTop(pinnedPage.position().top + hoveredOffset.x);
          //     $viewport.scrollLeft(pinnedPage.position().left + hoveredOffset.y);
          //   }
          // } else {
            this.model.set('viewScale', 1);
            this.viewScale(this.model.attributes.viewScale, false);
          // }
        } else {
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
      }
    },

    setBounds: _.throttle(function (e) {
      var bounds = {top: this.$el.scrollTop()};
      bounds.bottom = bounds.top + this.$el.height();
      this.model.set('bounds', bounds);
    }, 100),

    pinnedPageOrigin: function (page) {
      if (!page)
        return;

      return {
        x: page.$el.position().left,
        y: page.$el.position().top
      };
    },

    zoomToPage: function (page, scale) {
      var $viewport = $('.viewport-content');
      var view = this;

      this.model.set('scale', scale);
      var scaleDelta = this.model.attributes.scale / this.model.previous('scale');

      if (scaleDelta < 1) {
        // zoom out
        if (page) {
          var topOffset = Math.max(0, page.$el.position().top - this.$el.scrollTop());

          var pageIndex = parseInt(page.$el.data('page')) - 1;
          var oldLane = (pageIndex + (this.laneOffset || 0)) % this.scaleRatio(this.model.previous('scale'));
          var newLane = pageIndex % this.scaleRatio();
          if (oldLane >= (this.scaleRatio()-1)/2) {
            oldLane = this.scaleRatio() - (this.scaleRatio() - 1 - oldLane);
          }
          if (this.scaleRatio() > 2) {
            this.laneOffset = (oldLane - newLane + this.scaleRatio()) % this.scaleRatio();
            this.pagePlaceholder.css({width: 100 * this.model.attributes.scale * this.laneOffset + '%'});
          }
        } else {
          this.laneOffset = (oldLane - newLane + this.scaleRatio()) % this.scaleRatio();
          this.pagePlaceholder.css({width: 0});
        }
        this.pageScale(this.model.attributes.scale);
        if (page) {
          var pageOrigin = view.pinnedPageOrigin(page);
          if (oldLane >= (this.scaleRatio()-1)/2 || this.scaleRatio() == 2 && newLane == 1) {
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
        view.model.attributes.images.resetBounds();
        view.model.testVisible();
      }, 300);
    },
    viewScale: function (scale, animate, scaleOrigin) {
      var view = this;
      var scaleDelta = scale / (this.prevViewScale || 1);
      this.prevViewScale = scale;

      var $viewport = $('.viewport-content');
      var duration = 300;
      if (!scaleOrigin) {
        // scaleOrigin = {
        //   x: $viewport.width()/2,
        //   y: $viewport.height()/2,
        // };
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
            'margin-bottom': Math.max(0, (transformedOrigin.y + $viewport.height()) - $('.document-image-layout').height()) + 'px',
            transition: 'none',
          });
          $viewport.scrollLeft(transformedOrigin.x);
          $viewport.scrollTop(transformedOrigin.y);
          view.model.attributes.images.resetBounds();
          view.model.testVisible();
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
        scale = 1/(this.scaleRatio(scale) - 1);
        this.zoomToPage({$el: this.model.attributes.firstVisible.attributes.$el}, scale);
      } else {
        scale /= 0.75;
        scale = 1.5 * this.model.attributes.viewScale;
        this.smoothZoom(scale, {x: this.$el.width()/2, y: this.$el.height()/2});
      }
    },
    zoomOut: function () {
      var scale = this.model.attributes.scale * this.model.attributes.viewScale;
      if (scale <= 1) {
        scale = 1/Math.min(10, this.scaleRatio(scale) + 1);
        this.zoomToPage({$el: this.model.attributes.firstVisible.attributes.$el}, scale);
      } else {
        scale = 1/1.5 * this.model.attributes.viewScale;
        this.smoothZoom(scale, {x: this.$el.width()/2, y: this.$el.height()/2});
      }
    },
    goToPage: function (page) {
      var image = this.model.attributes.images.find(function (i) { return i.attributes.page == page; });
      if (image) {
        this.model.set('currentImage', image);
      }
    },
  });

  DraggingMixin.mixin(View);

  return View;
});
