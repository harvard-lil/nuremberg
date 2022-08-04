from nuremberg.core.tests.clientside_helpers import *

@pytest.fixture(scope='module')
def document(browser, unblocked_live_server):
    document_id = 1
    browser.get(unblocked_live_server.url + url('documents:show', kwargs={'document_id': document_id}))
    browser.execute_script("$('html').removeClass('touchevents'); $('html').removeClass('no-xhrresponsetypeblob'); Modernizr.touchevents = false; Modernizr.xhrresponsetypeblob = true;")
    assert 'List of Case 1 files, prosecution and defense, in English' in browser.title
    return browser

@pytest.fixture
def viewport(document):
    document.execute_script("$('.viewport-content').scrollTop(0);")
    return document.find_element_by_css_selector('.viewport-content')

@pytest.fixture
def log():
    print('BROWSER LOG:', document.get_log('browser'))

@pytest.fixture(scope='module')
def preloaded(document):
    # test preloading as a shared fixture to speed up the other tests

    img = wait(document, 5).until(presence_of_element_located(at('.document-image img')))
    # img.get_attribute('src').should.be.none # first image populates too soon

    # preload image as data-url
    wait(document, 10).until(element_has_attribute(img, 'src'))
    data_url = img.get_attribute('src')
    document.save_screenshot('screenshots/preload-first.png')
    assert 'data:image/jpeg;base64' in data_url
    assert len(data_url) == 148871

    # last image should not be downloaded yet
    img = document.find_element_by_css_selector('.document-image:last-child img')
    assert img.get_attribute('src') is None
    document.execute_script("$('.viewport-content').scrollTop(99999);")
    wait(document, 10).until(element_has_attribute(img, 'src'))
    document.save_screenshot('screenshots/preload-last.png')
    assert 'data:image/jpeg;base64' in img.get_attribute('src')

    return True

def test_zooming(document, viewport, preloaded):
    img = document.find_element_by_css_selector('.document-image img')

    # scroll mode
    document.find_element_by_css_selector('.tool-buttons .scroll').click()

    # image is full-width (mod scrollbars)
    document.save_screenshot('screenshots/full-size.png')
    assert img.size['width'] in range(viewport.size['width']-40, viewport.size['width'])

    # zoom out
    # context_click seems not to work?
    # ActionChains(document).move_to_element_with_offset(viewport, 50, 50).context_click().perform()
    document.find_element_by_css_selector('button.zoom-out').click()
    sleep(0.5)
    expected_scale = 1/2

    document.save_screenshot('screenshots/zoomed-out.png')
    assert int(img.size['width']) in range(int(viewport.size['width']*expected_scale-40), int(viewport.size['width']*expected_scale))

    # zoom in
    ActionChains(document).move_to_element(viewport).move_by_offset(50, 50).click().perform()
    sleep(0.5)
    ActionChains(document).move_to_element(viewport).move_by_offset(50, 50).click().perform()
    sleep(0.5)
    expected_scale = 1.5

    document.save_screenshot('screenshots/zoomed-in.png')
    assert int(img.size['width']) in range(int(viewport.size['width']*expected_scale-40), int(viewport.size['width']*expected_scale))


def test_page_navigation(document, viewport, preloaded):
    page = document.find_element_by_css_selector('.document-image[data-page="20"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .last-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/last-page.png')
    assert int(document.execute_script("return arguments[0].scrollTop;", viewport)) in range(int(offsetTop-25), int(offsetTop+25))

    page = document.find_element_by_css_selector('.document-image[data-page="19"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .prev-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/prev-page.png')
    assert int(document.execute_script("return arguments[0].scrollTop;", viewport)) in range(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="1"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .first-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/first-page.png')
    assert int(document.execute_script("return arguments[0].scrollTop;", viewport)) in range(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="2"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    document.find_element_by_css_selector('.page-buttons .next-page').click()
    sleep(0.1)
    document.save_screenshot('screenshots/next-page.png')
    assert int(document.execute_script("return arguments[0].scrollTop;", viewport)) in range(offsetTop-25, offsetTop+25)

    page = document.find_element_by_css_selector('.document-image[data-page="10"]')
    offsetTop = document.execute_script("return arguments[0].offsetTop;", page)
    select = Select(document.find_element_by_css_selector('.page-buttons select'))
    select.select_by_visible_text('Sequence No. 10')
    sleep(0.1)
    document.save_screenshot('screenshots/tenth-page.png')
    assert int(document.execute_script("return arguments[0].scrollTop;", viewport)) in range(offsetTop-25, offsetTop+25)
    assert '00001010.jpg' in document.find_element_by_css_selector('.page-buttons .download-page').get_attribute('href')


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
    assert 'HLSL Nuremberg Document #1 pages 1-20.pdf' in download
