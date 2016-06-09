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


  viewportView.on('currentPage', function () {
    toolbarView.setPageDownload(viewportView.model.attributes.currentImage.attributes.urls.full,
    'HLSL Nuremberg Document #' + viewportView.model.attributes.id + ' page ' + viewportView.model.attributes.currentImage.attributes.page + '.jpg');
  });

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

  $('.download-pdf').on('click', function () {
    $('.download-pdf').addClass('hide');
    $('.download-options').removeClass('hide');
    $('.download-options input[name=from-page]').val(1);
    $('.download-options input[name=to-page]').val(viewportView.model.attributes.totalPages);
  });
  $('.do-download').on('click', function () {
    var fromPage = parseInt($('.download-options input[name=from-page]').val());
    var toPage = parseInt($('.download-options input[name=to-page]').val());
    if (toPage < fromPage) {
      var t = toPage;
      toPage = fromPage;
      fromPage = t;
    }
    if (fromPage > viewportView.model.attributes.totalPages || toPage > viewportView.model.attributes.totalPages || fromPage < 1 || toPage < 1) {
      $('.download-options input[name=from-page]').val(1);
      $('.download-options input[name=to-page]').val(viewportView.model.attributes.totalPages);
      return;
    }

    var total = toPage - fromPage + 1;
    var loaded = 0;
    var done = false;

    $('.pdf-loading').removeClass('hide');
    $('.download-options').addClass('hide');
    $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");

    viewportView.preloadRange(fromPage, toPage)
    .done(function () {
      if (done) return;
      done = true;

      $('.pdf-loading .progress').text("Building PDF.");
      setTimeout(function () {
        var pdf = new jsPDF('p', 'in');
        var res = 75;
        pdf.deletePage(1);
        var images = viewportView.model.attributes.images.models;
        for (var i = fromPage - 1; i <= toPage - 1; i++) {
          var image = images[i];
          pdf.addPage(image.attributes.size.width / res, image.attributes.size.height / res);
          pdf.addImage(image.attributes.cache['full'] || image.attributes.cache['screen'], 'JPEG', 0, 0, image.attributes.size.width / res, image.attributes.size.height / res);

        }
        if (toPage === fromPage) {
          var pageLabel = ' page ' + toPage;
        } else {
          pageLabel = ' pages ' + fromPage + '-' + toPage;
        }
        pdf.save('HLSL Nuremberg Document #' + viewportView.model.attributes.id + pageLabel + '.pdf');
        $('.download-pdf').removeClass('hide');
        $('.pdf-loading').addClass('hide');
      }, 100);

    })
    .progress(function () {
      if (done) return;
      loaded += 1;
      $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");
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
