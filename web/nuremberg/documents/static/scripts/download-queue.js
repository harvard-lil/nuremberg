modulejs.define('DownloadQueue', function () {
  // download queue
  // conceptually this is a stack of queues, reorderable as a doubly-linked list with two priority pointers
  //
  // the document view sends a reset signal when the viewport changes to indicate that new
  // images should supercede ones requested previously
  //
  // queued pointer proceeds lifo, for the backlog
  // front pointer proceeds fifo, for images queued at the same time

  var concurrency = 5;

  var DownloadRequest = function (url, element) {
    var request = this;
    this.element = element;

    _.bindAll(this, 'xhrProgress');
    this.state = 'queued';
    this.url = url;
    this.promise = $.Deferred();
    this.promise.request = this;
    this.promise.cancel = function () {
      if (request.state === 'active') {
        if (request.xhr) {
          request.xhr.abort();
        }
      } else {
        request.state = 'cancelled';
      }
    };
  };
  DownloadRequest.enableXHR = true;
  DownloadRequest.failures = 0;

  DownloadRequest.prototype = {
    doDownload: function (fallback) {
      var request = this;
      this.state = 'active';

      if (Modernizr.xhrresponsetypeblob && DownloadRequest.enableXHR && !fallback) {
        // we can download images over ajax
        this.xhr = $.ajax({
          dataType: 'native',
          url: this.url,
          xhrFields: {
            responseType: 'blob',
            onprogress: this.xhrProgress,
          }
        });
        this.startTime = Date.now();
        this.promise.notify({loaded: 0, total: 1});
        this.xhr.then( function (result) {
          request.state = 'complete';
          request.promise.resolve(result);
        });
        this.xhr.fail( function (err, status) {
          if (status !== 'abort' && !fallback) {
            DownloadRequest.failures += 1;
            if (DownloadRequest.failures >= 5) {
              // Something's wrong, use fallback from now on
              DownloadRequest.enableXHR = false;
            }
            // this is probably because of cors, so use the fallback
            return request.doDownload(true);
          }

          request.state = 'failed';
          request.error = err;
          request.promise.reject(err);
        });
      } else {
        // fallback to using normal img loading
        this.element.src = this.url;
        var imgLoad = imagesLoaded(this.element, function () {
          if (imgLoad.images[0].isLoaded) {
            request.state = 'complete';
            request.promise.resolve('fallback');
          } else {
            request.state = 'failed';
            request.promise.reject({fallbackError: 'failed'});
          }
        })
      }
    },

    xhrProgress: function (event) {
      this.promise.notify(event);
    },
  };


  var DownloadQueue = {
    activeCount: 0,
    active: null,
    queued: null,
    requests: {},
    complete: {},

    download: function (url, element) {
      var request;
      request = this.requests[url];
      if (request) {
        if (request.state  === 'complete' || request.state === 'active') {
          return request.promise;
        } else if (request.state === 'queued') {
          this.moveToFront(request);
          return request.promise;
        }
      }

      request = new DownloadRequest(url, element);
      this.requests[url] = request;
      this.addToFront(request);
      this.testInterrupt();

      return request.promise;
    },

    refresh: function (promise) {
      var request = promise.request;
      if (request.state === 'queued') {
        this.moveToFront(request);
      }
    },

    activate: function (request) {
      if (this.activeCount >= concurrency)
        return;
      this.activeCount += 1;

      var queue = this;

      this.active = this.remove(request);
      request.doDownload();
      request.promise.always(function () {
        queue.activeCount -= 1;
        queue.active = null;
        queue.activateNext();
      });

      if (this.active === this.front) {
        this.front = null;
      }
    },

    activateNext: function () {
      if (this.queued && this.activeCount < concurrency) {
        if (this.queued.state === 'cancelled') {
          this.remove(this.queued);
          this.activateNext()
        } else {
          this.activate(this.queued);
        }
      }
    },

    addToFront: function (request) {
      if (this.activeCount < concurrency) {
        this.activate(request);
      } else if (!this.queued) {
        this.queued = request;
        this.front = request;
      } else if (!this.front) {
        // add front before queue
        request.next = this.queued;
        this.front = request;
        this.queued = request;
        request.next.prev = request;
      } else {
        // add after front
        request.next = this.front.next;
        this.front.next = request;
        request.prev = this.front;
        this.front = request;
        if (request.next)
          request.next.prev = request;
      }
    },

    moveToFront: function (request) {
      this.remove(request);
      this.addToFront(request);
    },

    remove: function (request) {
        var next = request.next;
        var prev = request.prev;

        if (this.queued === request)
          this.queued = next;
        if (this.front === request)
          this.front = next;
        if (next)
          next.prev = prev;
        if (prev)
          prev.next = next;

        request.next = null;
        request.prev = null;

        return request;
    },

    resetPriority: function () {
      this.front = null;
    },

    testInterrupt: function () {
      // TODO: interrupt an active request, if it's not very far along, to make room for a fresh one
    }
  };

  return DownloadQueue;
});
