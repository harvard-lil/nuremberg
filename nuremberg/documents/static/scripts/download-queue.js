modulejs.define('DownloadQueue', function () {
  // download queue
  // conceptually this is a stack of queues, reorderable as a doubly-linked list with two priority pointers
  // queued proceeds lifo, for the backlog
  // front pointer proceeds fifo, for images queued at the same time

  var concurrency = 5;

  var DownloadRequest = function (url) {
    var request = this;

    _.bindAll(this, 'xhrProgress');
    this.state = 'queued';
    this.url = url;
    this.promise = $.Deferred();
    this.promise.cancel = function () {
      if (request.state === 'active') {
        request.xhr.abort();
      }
    };
  };

  DownloadRequest.prototype = {
    doDownload: function () {
      var request = this;
      this.state = 'active';

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
      this.xhr.fail( function (err) {
        request.state = 'failed';
        request.error = err;
        request.promise.reject(err);
      });
    },

    xhrProgress: function (event) {
      this.progress =
      this.promise.notify(event);
    },
  };


  var DownloadQueue = {
    activeCount: 0,
    active: null,
    queued: null,
    requests: {},
    complete: {},

    download: function (url) {
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

      request = new DownloadRequest(url);
      this.requests[url] = request;
      this.addToFront(request);
      this.testInterrupt();

      return request.promise;
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
      if (this.queued && this.activeCount < concurrency)
        this.activate(this.queued);
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
      // todo, interrupt active request if it's not very far along
    }
  };

  return DownloadQueue;
});
