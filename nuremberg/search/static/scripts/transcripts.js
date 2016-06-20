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
  var batchSize = 11;

  $('.print-document').on('click', function () {
    window.print();
  });

  var goToSeq = function (seq) {
    currentSeq = Math.min(Math.max(seq, 1), totalPages);
    var $page = $viewport.find('.page[data-seq="'+currentSeq+'"]');
    $viewport.scrollTop($page[0].offsetTop - 10);
  };
  var goToPage = function (page) {
    var $page = $('.page[data-page="'+page+'"]');
    if ($page.length) {
      $viewport.scrollTop($page[0].offsetTop - 10);
      return true;
    }
    return false;
  };
  var goToDate = function (date) {
    var $page = $('.page[data-date="'+date+'"]');
    if ($page.length) {
      $viewport.scrollTop($page[0].offsetTop - 10);
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

  var highlightHtml = function (html, query) {
    if (!query)
      return;

    // extremely dirty way to highlight search terms in html
    // all terms that should be highlighted are between > and <
    // This will only highlight the first match in each paragraph.
    // This will not be perfect because our stems don't match solr's.

    var terms = query
    .replace(/\w+:.*/, '')
    .replace(/[^\w]+/g, ' ')
    .replace(/^\s+|\s+$/g, '')
    .replace(/\b[a-zA-Z]{1,2}\b/g, '')
    .replace(/(s|ing|ed|ment)\b/g, '')
    .split(/\ +/g);

    if (terms.length == 1 && terms[0] == '')
      return html.replace(/<\/?mark>/g, '');

    var rx = new RegExp( '>([^<>]*?)\\b('+terms.join('|')+')(s|ing|ed|ment)?\\b', 'ig');
    return html.replace(/<\/?mark>/g, '')
      .replace(rx, function (m, pre, term, post) {
        return '>' + pre + '<mark>' + term + (post || '') + '</mark>';
      });
  };

  var rehighlight = function () {
    $text.html(highlightHtml($text.html(), query));
  };

  rehighlight();
  $('input[name=q]').on('keyup', _.debounce(function () {
    query = this.value;
    rehighlight();
  }, 100));

  if (fromSeq <= 1) {
    $viewport.find('.above .end-indicator').text('Beginning of transcript')
  }
  if (toSeq >= totalPages) {
    $viewport.find('.below .end-indicator').text('End of transcript');
  }

  var loading = false;
  var loadBelow = function () {
    if (toSeq >= totalPages) {
      $viewport.find('.below .end-indicator').text('End of transcript');
      return;
    } else {
      $viewport.find('.below .end-indicator').text('Loading...');
    }
    if (loading)
      return;
    loading = true;
    $.get({
      url: location.pathname,
      data: {
        from_seq: toSeq,
        to_seq: Math.min(totalPages, toSeq + batchSize),
        partial: true,
      }
    })
    .then(function (data) {
      toSeq = data.to_seq;
      $text.append($(highlightHtml(data.html, query)));
      loading = false;
    })
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
        from_seq: Math.max(1, fromSeq - batchSize),
        to_seq: fromSeq,
        partial: true,
      }
    })
    .then(function (data) {
      fromSeq = data.from_seq;
      var container = $('<div></div>');
      container.append($(highlightHtml(data.html, query)));
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
      $text.append($(highlightHtml(data.html, query)));
      if (data.seq)
        goToSeq(data.seq)
      loading = false;
    })
  };

  $viewport.on('click', 'a.view-image', function () {
    var $a = $(this);
    var href = $a.siblings('.download-image').attr('href');
    $a.closest('.page-handle')
    .addClass('show')
    .after('<div><img src="'+ href +'" /></div>');
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

    if (currentDate)
      $('select.select-date').val(currentDate);

    if (currentPage)
      $('form.go-to-page input[name=page]').val(currentPage);
  };

  $viewport.on('scroll', _.throttle(handleScroll, 300));

})
