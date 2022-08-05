import os
import pytest
pytestmark = pytest.mark.django_db

from pytest_django.fixtures import live_server

from django.urls import reverse as url

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support.expected_conditions import *
from time import sleep

@pytest.fixture(scope='session')
def unblocked_live_server(request, django_db_blocker):
    """
    Workaround a db access error when using default live_server
    """
    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.block)
    return live_server.__wrapped__(request)

def at(selector):
    """
    Helper for wait locators.
    """
    return (By.CSS_SELECTOR, selector)

@pytest.fixture(scope="module")
def browser(request):
    """
    Fixture to connect to dockerized selenium instance
    """
    chrome_options = webdriver.ChromeOptions()
    browser = webdriver.Remote(command_executor="http://selenium:4444/wd/hub", options=chrome_options)
    browser.set_window_size(1200, 1024)

    request.addfinalizer(browser.quit)

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
        return driver.execute_script("return window['"+ self.name +"'];")
