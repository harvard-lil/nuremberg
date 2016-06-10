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
    toolbarView.setPageDownload(viewportView.model.attributes.currentImage.attributes.urls.full || viewportView.model.attributes.currentImage.attributes.urls.screen,
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


  var jsPDFLoaded = null;
  $('.download-pdf').on('click', function () {
    $('.download-pdf').addClass('hide');
    $('.download-options').removeClass('hide');
    $('.download-options input[name=from-page]').val(1);
    $('.download-options input[name=to-page]').val(viewportView.model.attributes.totalPages);
    if (!jsPDFLoaded)
      jsPDFLoaded = $.getScript(jsPDFURL);
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
    var coverPage = true;

    $('.pdf-loading').removeClass('hide');
    $('.download-options').addClass('hide');
    $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");

    var imagesLoaded = viewportView.preloadRange(fromPage, toPage);

    imagesLoaded.progress(function () {
      if (done) return;
      loaded += 1;
      $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");
    })

    $.when(jsPDFLoaded, imagesLoaded).then(function () {
      if (done) return;
      done = true;

      $('.pdf-loading .progress').text("Building PDF.");
      // wait a bit to render the message before locking up the thread
      setTimeout(function () {
        var pdf = new jsPDF('p', 'in');
        var res = 75;

        if (coverPage) {
          var weights = {
            300: 'light',
            400: 'normal',
            500: 'medium',
            600: 'bold',
          }
          var baseline = 1 * res;
          pdf.text(0.5, baseline/res, "Harvard Law School Library - Nuremberg Trials Project");
          baseline += 1/4 * res;
          $('.document-info').children('h3,h5,h6,p,br').each(function (n, child) {
            if (child.tagName === 'BR') {
              baseline += 15;
              return;
            }

            if (child.tagName === 'H3')
              baseline += 20;

            var $child = $(child);
            baseline += parseFloat($child.css('margin-top'));
            var fontFamily = $child.css('font-family').split(', ');
            var fontWeight = $child.css('font-weight');
            fontWeight = weights[fontWeight] || fontWeight;
            var fontSize = parseFloat($child.css('font-size')) - 3;
            var text = pdf
            .setFontType(fontWeight)
            .setFontSize(fontSize)
            .setFont(fontFamily[fontFamily.length - 1])
            .splitTextToSize(child.innerText, 7);

            pdf.text(0.5, baseline/res, text);
            baseline += (text.length + 1/2) * fontSize;
            // baseline += parseFloat($child.css('margin-bottom'));
          });
          baseline += 15;
          pdf.text(0.5, baseline/res, 'Pages ' + fromPage + ' to ' + toPage + ' included');
        } else {
          pdf.deletePage(1);
        }
        var images = viewportView.model.attributes.images.models;
        for (var i = fromPage - 1; i <= toPage - 1; i++) {
          var image = images[i];
          if (image.attributes.cache['full']) {
            url = image.attributes.cache['full']
            res = 300;
          } else {
            url = image.attributes.cache['screen'];
            res = 75;
          }
          pdf.addPage(image.attributes.size.width / res, image.attributes.size.height / res);
          pdf.addImage(url, 'JPEG', 0, 0, image.attributes.size.width / res, image.attributes.size.height / res);

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

    });
  });

  $('.clear-search').on('click', function (e) {
    e.preventDefault();
    $(this).closest('form').find('input[type="search"]').val('');
  });

  $('.document-viewer .clear-search').on('click', function (e) {
    $(this).closest('.document-tools').hide().next('hr').hide();
  });
});
