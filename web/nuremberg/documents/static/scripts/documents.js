modulejs.define('documents', ['DocumentViewport', 'DocumentTools', 'DownloadPDF'], function (DocumentViewport, DocumentTools, DownloadPDF) {
  var viewportView = new DocumentViewport;
  var toolbarView = new DocumentTools({el: $('.document-tools')});
  var overlayView = new DocumentTools({el: $('.document-tools-overlay')});

  toolbarView.on('zoomIn', viewportView.zoomIn);
  toolbarView.on('zoomOut', viewportView.zoomOut);
  toolbarView.on('goToPage', viewportView.goToPage);

  overlayView.on('setTool', viewportView.setTool);
  overlayView.on('toggleExpand', viewportView.toggleExpand);

  viewportView.on('currentPage', function (page) {
    if (page == 1) {
      var pageHash = '#p.1';
    } else {
      pageHash = '#p.' + page;
    }
    if (history && history.replaceState) {
      history.replaceState(undefined, undefined, pageHash);
    } else {
      location.hash = pageHash;
    }
    toolbarView.setPage(page);
    toolbarView.setPageDownload(viewportView.model.attributes.currentImage.attributes.urls.full || viewportView.model.attributes.currentImage.attributes.urls.screen,
    'HLSL Nuremberg Document #' + viewportView.model.attributes.id + ' page ' + viewportView.model.attributes.currentImage.attributes.page + '.jpg');
  });

  if (location.hash) {
    var match = location.hash.match(/p\.(\d+)/);
    if (match)
    viewportView.goToPage(match[1]);
  }

  $('.download-pdf').on('click', function () {
    $('.download-pdf').addClass('hide');
    $('.download-options').removeClass('hide');
    $('.download-options input[name=from-page]').val(1);
    $('.download-options input[name=to-page]').val(viewportView.model.attributes.totalPages);
    modulejs.require('JSPDFLoaded');
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

    DownloadPDF(viewportView, fromPage, toPage);
  });

  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('');
  });

  $('.document-viewer .clear-search').on('click', function (e) {
    $(this).closest('.document-tools').hide().next('hr').hide();
  });
});
