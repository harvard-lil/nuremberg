from nuremberg.core.tests.clientside_helpers import *

@pytest.fixture(scope='module')
def document(browser, live_server):
    document_id = 1
    browser.get(live_server.url + url('documents:show', kwargs={'document_id': document_id}))
    browser.execute_script("$('html').removeClass('touchevents'); Modernizr.touchevents = false;")
    browser.title.should.contain('List of Case 1 documents, prosecution and defense, in English.')
    return browser

@pytest.fixture
def viewport(document):
    document.execute_script("$('.viewport-content').scrollTop(0);")
    return document.find_element_by_css_selector('.viewport-content')

@pytest.fixture(scope='module')
def preloaded(document):
    # test preloading as a shared fixture to speed up the other tests

    img = wait(document, 5).until(presence_of_element_located(at('.document-image img')))
    img.get_attribute('src').should.be.none

    # preload image as data-url
    wait(document, 10).until(element_has_attribute(img, 'src'))
    data_url = img.get_attribute('src')
    document.save_screenshot('screenshots/preload-first.png')
    data_url.should.contain('data:image/jpeg;base64')
    len(data_url).should.equal(148871)

    # last image should not be downloaded yet
    img = document.find_element_by_css_selector('.document-image:last-child img')
    img.get_attribute('src').should.be.none
    document.execute_script("$('.viewport-content').scrollTop(99999);")
    wait(document, 10).until(element_has_attribute(img, 'src'))
    document.save_screenshot('screenshots/preload-last.png')
    img.get_attribute('src').should.contain('data:image/jpeg;base64')

    return True

def test_zooming(document, viewport, preloaded):
    img = document.find_element_by_css_selector('.document-image img')

    # scroll mode
    document.find_element_by_css_selector('.tool-buttons .scroll').click()

    # image is full-width (mod scrollbars)
    document.save_screenshot('screenshots/full-size.png')
    img.size['width'].should.be.within(viewport.size['width']-40, viewport.size['width'])

    # zoom out
    # context_click seems not to work?
    # ActionChains(document).move_to_element_with_offset(viewport, 50, 50).context_click().perform()
    document.find_element_by_css_selector('button.zoom-out').click()
    sleep(0.5)
    expected_scale = 1/2

    document.save_screenshot('screenshots/zoomed-out.png')
    img.size['width'].should.be.within(viewport.size['width']*expected_scale-40, viewport.size['width']*expected_scale)

    # zoom in
    ActionChains(document).move_to_element_with_offset(viewport, 50, 50).click().perform()
    sleep(0.5)
    ActionChains(document).move_to_element_with_offset(viewport, 50, 50).click().perform()
    sleep(0.5)
    expected_scale = 1.5

    document.save_screenshot('screenshots/zoomed-in.png')
    img.size['width'].should.be.within(viewport.size['width']*expected_scale-40, viewport.size['width']*expected_scale)


def test_page_navigation(document, viewport, preloaded):
    page = document.find_element_by_css_selector('.document-image[data-page="20"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .last-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/last-page.png')
    int(document.execute_script("return arguments[0].scrollTop;", viewport)).should.be.within(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="19"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .prev-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/prev-page.png')
    int(document.execute_script("return arguments[0].scrollTop;", viewport)).should.be.within(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="1"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .first-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/first-page.png')
    int(document.execute_script("return arguments[0].scrollTop;", viewport)).should.be.within(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="2"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .next-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/next-page.png')
    int(document.execute_script("return arguments[0].scrollTop;", viewport)).should.be.within(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="10"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    select = Select(document.find_element_by_css_selector('.page-buttons select'))
    select.select_by_visible_text('Sequence No. 10')
    sleep(0.1)
    document.save_screenshot('screenshots/tenth-page.png')
    int(document.execute_script("return arguments[0].scrollTop;", viewport)).should.be.within(offsetTop-25, offsetTop+25)


def test_pdf_generation(document, preloaded):
    # extremely ugly shim to detect PDF save
    document.execute_script("""
        var _cENS = document.createElementNS;
        document.createElementNS = function () {
            document.createElementNS = _cENS;
            window.save_link = document.createElementNS.apply(document, arguments);
            window.save_link.dispatchEvent = function () {
                window.save_link_clicked = true;
            };
            document.body.appendChild(window.save_link);
            return window.save_link;
        }""")

    document.find_element_by_css_selector('button.download-pdf').click()
    inner_save_link = wait(document, 10).until(global_variable_exists('save_link'))
    save_link = wait(document, 1).until(visibility_of_element_located(at('.download-options a')))
    save_link.click()
    document.save_screenshot('screenshots/building-pdf.png')
    download = wait(document, 30).until(element_has_attribute(inner_save_link, 'download'))
    download.should.contain('HLSL Nuremberg Document #1 pages 1-20.pdf')
