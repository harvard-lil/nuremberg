modulejs.define('JSPDFLoaded', function () {
  // promise that indicates when the jsPDF global will be available
  return $.getScript(jsPDFURL);
});

modulejs.define('DownloadPDF', function () {
  // PDF builder
  // 1. download all images in range
  // 2. wait for jsPDF script to load
  // 3. build a cover page from document info
  // 4. assemble PDF
  var coverPage = true;

  var DownloadPDF = function (viewportView, fromPage, toPage) {
    var total = toPage - fromPage + 1;
    var loaded = 0;

    $('.pdf-loading').removeClass('hide');
    $('.download-options').addClass('hide');
    $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");

    var imagesLoaded = viewportView.preloadRange(fromPage, toPage);
    imagesLoaded.progress(function () {
      loaded += 1;
      $('.pdf-loading .progress').text(loaded + "/" + total + " loaded");
    })

    $.when(modulejs.require('JSPDFLoaded'), imagesLoaded).then(function () {
      $('.pdf-loading .progress').text("Building PDF.");
      // wait a bit to render the message before locking up the thread
      setTimeout(function () {BuildPDF(viewportView, fromPage, toPage)}, 100);
    });
  };

  var BuildPDF = function (viewportView, fromPage, toPage) {
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
        // res = 300;
      } else {
        url = image.attributes.cache['screen'];
        // res = 75;
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
  };

  return DownloadPDF;
});
