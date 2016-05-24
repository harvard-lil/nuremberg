modulejs.define('search', function () {
  $('.date-slider').slider({
    range: true,
    min: 1898,
    max: 1948,
    values: [1923, 1940],
    slide: function (e, ui) {
      $('input[name="year_min"]').val(ui.values[0]);
      $('input[name="year_max"]').val(ui.values[1]);
    }
  });

  $('.facet .collapse').on('click', function () {
    $(this).closest('.facet').toggleClass('collapsed');
  });
})
