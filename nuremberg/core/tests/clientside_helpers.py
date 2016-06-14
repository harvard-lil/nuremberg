import os
import pytest
pytestmark = [pytest.mark.live_server, pytest.mark.django_db(transaction=False)]

import sure
from django.core.urlresolvers import reverse as url

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.expected_conditions import *
from time import sleep

def at(selector):
    """
    Helper for wait locators.
    """
    return (By.CSS_SELECTOR, selector)

@pytest.fixture(scope="module")
def browser(request):
    """
    Fixture to reliably close phantomjs after test completes.
    """
    browser = webdriver.PhantomJS()
    browser.set_window_size(1200, 900)
    def quit():
        browser.quit()
        os.system('pgrep phantomjs | xargs kill')
    request.addfinalizer(quit)
    return browser

class element_has_attribute(object):
    """
    Selenium expected condition to wait for img attributes.
    """
    def __init__(self, element, attribute):
        self.element = element
        self.attribute = attribute

    def __call__(self, driver):
        return self.element.get_attribute(self.attribute)


class global_variable_exists(object):
    """
    Selenium expected condition to wait for js variables.
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, driver):
        print("return window['"+ self.name +"'];", driver.execute_script("return window['"+ self.name +"'];"))
        return driver.execute_script("return window['"+ self.name +"'];")
