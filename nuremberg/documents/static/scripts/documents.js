modulejs.define('documents', ['DocumentViewport', 'DocumentTools'], function (DocumentViewport, DocumentTools) {
  var viewportView = new DocumentViewport;
  var toolbarView = new DocumentTools({el: $('.document-tools')});
  var overlayView = new DocumentTools({el: $('.document-tools-overlay')});

  if (location.hash) {
      var match = location.hash.match(/page-(\d)+/);
      if (match)
        viewportView.goToPage(match[1]);
  }

  toolbarView.on('zoomIn', viewportView.zoomIn);
  toolbarView.on('zoomOut', viewportView.zoomOut);
  toolbarView.on('goToPage', viewportView.goToPage);

  overlayView.on('setTool', viewportView.setTool);
  overlayView.on('toggleExpand', viewportView.toggleExpand);

  viewportView.on('currentPage', toolbarView.setPage);

  $('.print-document').on('click', function () {
    $('.print-document').addClass('hide');
    $('.print-loading').removeClass('hide');
    var loaded = 0;
    var total = viewportView.$el.find('img').length;
    $('.print-loading .progress').text(loaded + "/" + total + " loaded");
    viewportView.hardloadAll();
    viewportView.$el.imagesLoaded()
    .done(function () {
      viewportView.zoomToFit();
      window.print();
      $('.print-document').removeClass('hide');
      $('.print-loading').addClass('hide');
    })
    .progress(function () {
      loaded += 1;
      $('.print-loading .progress').text(loaded + "/" + total + " loaded");
    })
  });

  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('');
  });
  $('.document-viewer .clear-search').on('click', function (e) {
    $(this).closest('.document-tools').hide().next('hr').hide();
  });
});
