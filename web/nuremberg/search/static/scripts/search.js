modulejs.define('search', function () {
  var spinnerOptions = {
    lines: 17 // The number of lines to draw
    , length: 3 // The length of each line
    , width: 3 // The line thickness
    , radius: 10 // The radius of the inner circle
    , scale: 1 // Scales overall size of the spinner
    , corners: 1 // Corner roundness (0..1)
    , color: '#9ec0c1' // #rgb or #rrggbb or array of colors
    , opacity: 0.25 // Opacity of the lines
    , rotate: 0 // The rotation offset
    , direction: 1 // 1: clockwise, -1: counterclockwise
    , speed: 1 // Rounds per second
    , trail: 60 // Afterglow percentage
    , fps: 15 // Frames per second when using setTimeout() as a fallback for CSS
    , zIndex: 2e9 // The z-index (defaults to 2000000000)
    , className: 'spinner' // The CSS class to assign to the spinner
    , top: '50%' // Top position relative to parent
    , left: '40px' // Left position relative to parent
    , shadow: false // Whether to render a shadow
    , hwaccel: false // Whether to use hardware acceleration
    , position: 'absolute' // Element positioning
  }
  var SearchView = Backbone.View.extend({
    el: 'main',
    initialize: function () {
      var $dateForm = $('.date-filter-form').on('submit', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var fromYear = $dateForm.find('input[name=year_min]').val();
        var toYear = $dateForm.find('input[name=year_max]').val();

        if (fromYear < 1895 || fromYear > 1950 || toYear < 1895 || toYear > 1950) {
          fromYear = Math.min(Math.max(fromYear, 1895), 1950);
          toYear = Math.min(Math.max(toYear, 1895), 1950);
          $dateForm.find('input[name=year_min]').val(fromYear);
          $dateForm.find('input[name=year_max]').val(toYear);
          return;
        }

        if (fromYear > toYear) {
          var t = fromYear;
          fromYear = toYear;
          toYear = t;
          $dateForm.find('input[name=year_min]').val(fromYear);
          $dateForm.find('input[name=year_max]').val(toYear);
        }

        var range = 'f=date_year:'+fromYear+'-'+toYear;
        if (location.search && location.search.indexOf('date_year') > -1)
          href = location.search.replace(/f=date_year:\d+-?\d+/, range)
        else if (location.search.indexOf('?') > -1)
          href = location.search + '&' + range;
        else
          href = '?' + range;
        href = href.replace(/([\?&])page=\d+&?/, function (m, c) {return c});
        gotoResults(href);
      });

      // set date range to extent of date facets
      if (!$dateForm.find('input[name=year_min]').val()) {
        var min = _.min($dateForm.closest('.facet').find('p[data-year]'), function (p) { return $(p).data('year') || Infinity });
        min = min && $(min).data('year') ? $(min).data('year') : 1900;
        $dateForm.find('input[name=year_min]').val(min);
      }
      if (!$dateForm.find('input[name=year_max]').val()) {
        var max = _.max($dateForm.closest('.facet').find('p[data-year]'), function (p) { return $(p).data('year') || 0 });
        max = max && $(max).data('year') ? $(max).data('year') : 1945;
        $dateForm.find('input[name=year_max]').val(max);
      }

      var setRange = _.debounce(function () {
          $dateForm.triggerHandler('submit');
      }, 700);

      $('.date-slider').slider({
        range: true,
        min: 1898,
        max: 1948,
        values: [$dateForm.find('input[name=year_min]').val(), $dateForm.find('input[name=year_max]').val()],
        slide: function (e, ui) {
          $('input[name="year_min"]').val(ui.values[0]);
          $('input[name="year_max"]').val(ui.values[1]);
          setRange();
        },
      });

      if (location.hash === '#advanced') {
        $('.advanced-search-help').removeClass('hide');
      }

      $('.show-advanced-search, .hide-advanced-search').on('click', function () {
        $('.advanced-search-help').toggleClass('hide');
        var hash = '#' + ($('.advanced-search-help').hasClass('hide') ? '': 'advanced');
        if (history && history.replaceState) {
          history.replaceState(undefined, undefined, hash);
        } else {
          location.hash = hash;
        }
      });

      $('.facet .collapse').on('click', function () {
        $(this).closest('.facet').toggleClass('collapsed');
      });

      $('.clear-search').on('click', function (e) {
        e.preventDefault();
        $form = $(this).closest('form')
        $form.find('input[type="search"]').val('');
        submitForm($form);
      });

      $('.facet .show-all').on('click', function () {
        $(this).addClass('hide')
        .closest('.facet').children('p').removeClass('hide');
      });

      $('.results-sort select').on('change', function () {
        gotoResults($(this).val());
      });
    }
  });

  var searchView = new SearchView({el: $('main')});

  var currentLoad = null;
  var loadingTimeout = null;

  var loadResults = function (href) {
    if (currentLoad) {
      currentLoad.abort();
      clearTimeout(loadingTimeout);
    }
    loadingTimeout = setTimeout( function () {
        var $indicator = $('.loading-indicator').removeClass('hide');
        $indicator.find('.spinner').remove();
        new Spinner(spinnerOptions).spin($indicator[0]);
        $('.results-count').addClass('hide');
        loadingTimeout = setTimeout(function () {
          $('<a>')
          .addClass('force-load')
          .attr('href', href)
          .text('This is taking unusually long. Click here to load results manually.')
          .appendTo($indicator);
        }, 7000);
    }, 100);
    currentLoad = $.ajax({
      url: href,
      data: {'partial': true}
    });
    currentLoad.then(function (html) {
      clearTimeout(loadingTimeout);
      currentLoad = null;
      loadingTimeout = null;
      $('main').html(html);
      searchView = new SearchView({el: $('main')});
    })
    .fail(function (xhr, status) {
      if (status !== 'abort') {
        // fallback to normal page load
        location.href = href;
      }
    })
  }

  var gotoResults = function (href) {
    if (location.search === href) {
      return;
    }
    if (history && history.pushState) {
      history.pushState(undefined, undefined, href);
    }
    loadResults(href);
  }

  window.onpopstate = function (event) {
    loadResults(location.search, true);
  }

  var tabClicking = function (e) {
    return ( e.ctrlKey || e.metaKey || (e.button && e.button == 1));
  }

  $(document).on('click', 'a', function (e) {
    // Considering navigating away? Consider... not.
    if (tabClicking(e)) return;
    var $a = $(this);
    var href = $a.attr('href');
    if ($a.hasClass('force-load')) {
      return;
    }
    if (href && href.match(/^\/search|^\?/)) {
      e.preventDefault();
      gotoResults(href);
    }
  });

  $(document).on('click', 'a.page-number', function () {
    $(document).scrollTop($('.results-count').offset().top);
  });

  var submitForm = function ($form) {
    var action = $form.attr('action');
    if (!action || action == location.pathname) {
      gotoResults('?' + $form.serialize());
      return false;
    }
    return true;
  }
  $(document).on('submit', 'form', function (e) {
    if (tabClicking(e)) return;
    var $form = $(this);
    return submitForm($form);
  });
})
