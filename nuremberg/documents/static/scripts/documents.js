modulejs.define('documents', function () {
  // $('#document-viewport').on('mousewheel', function (event) {
  //   var direction = event.originalEvent.wheelDeltaY;
  //   var $viewport = $('#document-viewport');
  //   var scrollTop = $(document).scrollTop();
  //   var scrollBottom = scrollTop + $(window).height();
  //   var viewportTop = $viewport.offset().top;
  //   var viewportBottom = viewportTop + $viewport.height();
  //   if ((direction < 0 && scrollBottom >= viewportBottom)
  //     || (direction > 0 && scrollTop <= viewportTop))
  //   {
  //     $('#document-viewport').addClass('scrollable').focus();
  //   } else {
  //     $('#document-viewport').removeClass('scrollable');
  //   }
  // });

  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('');
  });
  $('.document-viewer .clear-search').on('click', function (e) {
    $(this).closest('.document-tools').hide().next('hr').hide();
  });
});
