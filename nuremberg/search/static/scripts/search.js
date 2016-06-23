modulejs.define('search', function () {
  var $dateForm = $('.date-filter-form').on('submit', function (e) {
    e.preventDefault();
    var fromYear = $dateForm.find('input[name=year_min]').val();
    var toYear = $dateForm.find('input[name=year_max]').val();
    var range = 'f=date_year:'+fromYear+'-'+toYear;
    if (location.search && location.search.indexOf('date_year') > -1)
    location.search = location.search.replace(/f=date_year:\d+-\d+/, range)
    else if (location.search.indexOf('?') > -1)
    location.search += '&' + range;
  });

  $('.date-slider').slider({
    range: true,
    min: 1898,
    max: 1948,
    values: [$dateForm.find('input[name=year_min]').val(), $dateForm.find('input[name=year_max]').val()],
    slide: function (e, ui) {
      $('input[name="year_min"]').val(ui.values[0]);
      $('input[name="year_max"]').val(ui.values[1]);
    }
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
    $(this).closest('form').find('input[type="search"]').val('');
  });

  $('.facet .show-all').on('click', function () {
    $(this).addClass('hide')
    .closest('.facet').children('p').removeClass('hide');
  });

  $('.results-sort select').on('change', function () {
    location.href = $(this).val();
  });
})
