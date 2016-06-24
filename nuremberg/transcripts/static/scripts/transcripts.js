modulejs.define('transcript-search', function () {
  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('');
  });
});
modulejs.define('transcript-viewer', function () {
  var $viewport = $('.viewport-content');

  var $text = $viewport.find('.transcript-text');
  var currentSeq = $text.data('seq');
  var currentDate;
  var currentPage;
  var count = $text.data('page-count');
  var totalPages = $text.data('total-pages');
  var fromSeq = $text.data('from-seq');
  var toSeq = $text.data('to-seq');
  var query = $('input[name=q]').val();
  var batchSize = 10;

  $('.print-document').on('click', function () {
    $('.print-options, .print-document').toggleClass('hide');
  });
  $('.do-print').on('click', function () {
    var pages = parseInt($('.print-options input[name=pages]').val());
    if (pages > 20 || pages < 1) {
      pages = Math.min(Math.max(pages, 1), 20);
      return $('.print-options input[name=pages]').val(pages);
    }
    var missing = currentSeq + pages - toSeq;
    if (missing > 1)
      var promise = loadBelow(Math.ceil(missing/10));
    if (promise) {
      promise.then(function () {doPrint(pages)});
    } else {
      doPrint(pages);
    }
  })
  var intcomma = function (x) {
      return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  var doPrint = function (pages) {
    var $hidden = $('.page').addClass('print-hide');
    var nums = [0,0];
    var seqs = [0,0];
    var printed = 0;
    for (var i = currentSeq; i <= currentSeq + pages - 1; i++) {
      var shown = $hidden.filter('[data-seq="'+i+'"]');
      shown.removeClass('print-hide');
      if (shown.length) {
        nums[0] = nums[0] || shown.data('page') || '?';
        nums[1] = shown.data('page') || '?';
        seqs[0] = seqs[0] || shown.data('seq');
        seqs[1] = shown.data('seq');
        printed += 1;
      }
    }
    $('.document-info .print-show').text('Printed '+printed+' transcript pages labeled '+_.map(nums, intcomma).join(' through ')+' (seq. nos. '+seqs.join('-')+')' )

    $('.print-options, .print-document').toggleClass('hide');
    window.print();
    $hidden.removeClass('print-hide');
  }

  var goToSeq = function (seq) {
    currentSeq = Math.min(Math.max(seq, 1), totalPages);
    var $page = $viewport.find('.page[data-seq="'+currentSeq+'"]');
    $viewport.scrollTop($page[0].offsetTop - 10);
    if (history && history.replaceState) {
      history.replaceState(undefined, undefined, location.pathname + location.search.replace(/seq=\d+/, 'seq='+seq))
    }
  };
  var goToPage = function (page) {
    var $page = $('.page[data-page="'+page+'"]');
    if ($page.length) {
      goToSeq($page.data('seq'));
      return true;
    }
    return false;
  };
  var goToDate = function (date) {
    var $page = $('.page[data-date="'+date+'"]');
    if ($page.length) {
      goToSeq($page.data('seq'));
      return true;
    }
    return false;
  };

  var initialSeq = currentSeq;
  goToSeq(initialSeq);
  setTimeout(function () {goToSeq(initialSeq);}, 100);

  $('.page-buttons .next-page').on('click', function () {
    goToSeq(currentSeq + 1);
  });
  $('.page-buttons .prev-page').on('click', function () {
    goToSeq(currentSeq - 1);
  });

  $('.page-buttons .first-page').on('click', function () {
    if (fromSeq <= 1) {
      goToSeq(1);
    } else {
      loadFromScratch({seq: 1});
    }
  });
  $('.page-buttons .last-page').on('click', function () {
    if (fromSeq >= totalPages) {
      goToSeq(1);
    } else {
      loadFromScratch({seq: totalPages});
    }
  });
  $('form.go-to-page').on('submit', function (e) {
    e.preventDefault();

    var $input = $(this).find('input[name=page]')
    var page = $input.val();
    if (page < 1)
      return $input.val(1);
    if (page > totalPages)
      return $input.val(totalPages);
    var $page = $('.page[data-page="'+page+'"]');

    if (!goToPage(page))
      loadFromScratch({page: page});
  });
  $('select.select-date').on('change', function () {
    var date = $(this).val();
    if (!goToDate(date))
      loadFromScratch({date: date});
  });

  var highlightEl = function (el, query) {
    el.find('mark').contents().unwrap();
    if (!query)
      return;

    // rough highlighting of terms in javascript

    var terms = query
    .replace(/evidence:|exhibit:/, '')
    .replace(/\w+:.*/, '')
    .replace(/[^\w\-]+/g, ' ')
    .replace(/^\s+|\s+$/g, '')
    .replace(/(s|ing|ed|ment)\b/g, '')
    .split(/\ +/g);

    terms = _.reject(terms, function (term) {return !term || (term.length < 3 && !term.match(/[A-Z]{2,3}|\d+/));});

    if (!terms.length)
      return;

    var rx = new RegExp( '\\b('+terms.join('|')+')(s|ing|ed|ment)?\\b', 'ig');
    el.find('p, span, a').contents().filter(function(){ return this.nodeType == 3; }).replaceWith(function (n, text) {
        return this.textContent.replace(rx, function (m, term, stem) {
            return '<mark>' + term + (stem || '') + '</mark>';
        });
    });
  };

  var rehighlight = function () {
    $text.html(highlightEl($text, query));
  };

  rehighlight();
  $('input[name=q]').on('keyup', _.debounce(function () {
    query = this.value;
    rehighlight();
  }, 500));
  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('').trigger('keyup')
  });

  var loading = false;
  var loadBelow = function (batches) {
    batches = batches || 1;
    if (toSeq >= totalPages) {
      $viewport.find('.below .end-indicator').text('End of transcript');
      return;
    } else {
      $viewport.find('.below .end-indicator').text('Loading...');
    }
    if (loading)
      return;
    loading = true;
    return $.get({
      url: location.pathname,
      data: {
        from_seq: toSeq,
        to_seq: Math.min(totalPages, toSeq + batches * (batchSize) + 1),
        partial: true,
      }
    })
    .then(function (data) {
      toSeq = data.to_seq;
      var container = $('<div></div>');
      container.append($(data.html));
      highlightEl(container, query);
      $text.append(container);
      loading = false;
    });
  };

  var loadAbove = function () {
    if (fromSeq <= 1) {
      $viewport.find('.above .end-indicator').text('Beginning of transcript');
      return;
    } else {
      $viewport.find('.above .end-indicator').text('Loading...');
    }
    if (loading)
    return;
    loading = true;
    $.get({
      url: location.pathname,
      data: {
        from_seq: Math.max(1, fromSeq - (batchSize + 1)),
        to_seq: fromSeq,
        partial: true,
      }
    })
    .then(function (data) {
      fromSeq = data.from_seq;
      var container = $('<div></div>');
      container.append($(data.html));
      highlightEl(container, query);
      $text.prepend(container);
      $viewport.scrollTop($viewport.scrollTop() + container.height() + 29);
      loading = false;
    })
  };


  var loadFromScratch = function (options) {
    if (loading)
      return;
    options.partial = true;
    options.seq = options.seq || currentSeq;
    loading = true;
    $text.empty();
    $.get({
      url: location.pathname,
      data: options
    })
    .then(function (data) {
      fromSeq = data.from_seq;
      toSeq = data.to_seq;
      $text.append(data.html);
      rehighlight();
      if (data.seq)
        goToSeq(data.seq)
      loading = false;
    })
  };

  if (fromSeq <= 1) {
    loadAbove();
  }
  if (toSeq >= totalPages) {
    loadBelow();
  }

  $viewport.on('click', 'a.view-image', function (e) {
    var $handle = $(this).closest('.page-handle')
    var href = $handle.find('.download-image').attr('href');
    if (!$handle.hasClass('has-image')) {
      $handle
      .addClass('has-image')
      .after('<div class="page-image hide"><img src="'+ href +'" /></div>');
    }
    $img = $handle.next('.page-image');
    $img.toggleClass('hide');
    if ($img.hasClass('hide')) {
      $handle.removeClass('show');
      $handle.find('a.view-image').text('VIEW');
    } else {
      $handle.addClass('show');
      $handle.find('a.view-image').text('HIDE');
    }
    e.stopPropagation();
  });

  $viewport.on('click', '.page-handle', function () {
    $(this).addClass('show');
  });

  var handleScroll = function () {
    var view = {
      top: $viewport.scrollTop(),
      height: $viewport.height() * 2,
      bottom: $viewport.scrollTop() + $viewport.height()
    };

    var page = {
      top: 0,
      bottom: $viewport[0].scrollHeight
    };

    if (view.bottom + view.height > page.bottom) {
      loadBelow();
    } else if (view.top - view.height < page.top) {
      loadAbove();
    }
    var rect = $viewport[0].getBoundingClientRect();
    var point = {x: rect.left + 100, y: rect.top + 10};
    do {
      point.y += 100;
      if (point.y > rect.top + 1000) return;
      var target = document.elementFromPoint(point.x, point.y);
      var $page = $(target).closest('.page');
    } while ($page.length == 0)

    currentSeq = $page.data('seq');
    currentPage = $page.data('page');
    currentDate = $page.data('date');

    if (currentSeq && history && history.replaceState) {
      history.replaceState(undefined, undefined, location.pathname + location.search.replace(/seq=\d+/, 'seq='+currentSeq))
    }

    if (currentDate)
      $('select.select-date').val(currentDate);

    if (currentPage)
      $('form.go-to-page input[name=page]').val(currentPage);
  };

  $viewport.on('scroll', _.throttle(handleScroll, 300));

})
