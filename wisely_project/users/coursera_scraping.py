__author__ = 'tmehta'
import argparse
import getpass
import json
import netrc
import os
import platform
import re
import requests
import shutil
import sys
import tarfile
import time
import math
from bs4 import BeautifulSoup
from os import path
from six import print_


class CourseraDownloader(object):
    """
    Class to download content (videos, lecture notes, ...) from coursera.org for
    use offline.

    https://github.com/dgorissen/coursera-dl

    :param username: username
    :param password: password
    :keyword proxy: http proxy, eg: foo.bar.com:1234
    :keyword parser: xml parser
    :keyword ignorefiles: comma separated list of file extensions to skip (e.g., "ppt,srt")
    """
    LIST_PAGE = 'https://www.coursera.org/'
    BASE_URL = 'https://class.coursera.org/%s'
    HOME_URL = BASE_URL + '/class/index'
    LECTURE_URL = BASE_URL + '/lecture/index'
    QUIZ_URL = BASE_URL + '/quiz/index'
    AUTH_URL = BASE_URL + "/auth/auth_redirector?type=login&subtype=normal"
    LOGIN_URL = "https://accounts.coursera.org/api/v1/login"
    ABOUT_URL = "https://www.coursera.org/maestro/api/topic/information?topic-id=%s"

    # see
    # http://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
    DEFAULT_PARSER = "html.parser"

    # how long to try to open a URL before timing out
    TIMEOUT = 30.0

    def __init__(self, username,
                 password,
                 proxy=None,
                 parser=DEFAULT_PARSER,
                 ignorefiles=None,
                 max_path_part_len=None,
                 gzip_courses=False,
                 wk_filter=None):

        self.username = username
        self.password = password
        self.parser = parser

        # Split "ignorefiles" argument on commas, strip, remove prefixing dot
        # if there is one, and filter out empty tokens.
        self.session = None
        self.proxy = proxy

        try:
            self.wk_filter = map(
                int, wk_filter.split(",")) if wk_filter else None
        except Exception as e:
            print_("Invalid week filter, should be a comma separated list of integers", e)
            exit()

    def login(self, className):
        """
        Login into coursera and obtain the necessary session cookies.
        """
        s = requests.Session()
        if self.proxy:
            s.proxies = {'http': self.proxy}

        url = self.lecture_url_from_name(className)
        res = s.get(url, timeout=self.TIMEOUT)
        if res.status_code == 404:
            raise Exception("Unknown class %s" % className)
        res.close()

        # get the csrf token
        if 'csrf_token' not in s.cookies:
            raise Exception("Failed to find csrf cookie")

        # call the authenticator url
        LOGIN_FORM = {'email': self.username, 'password': self.password}
        s.headers['Referer'] = 'https://www.coursera.org'
        s.headers['X-CSRFToken'] = s.cookies.get('csrf_token')
        s.cookies['csrftoken'] = s.cookies.get('csrf_token')

        res = s.post(self.LOGIN_URL, data=LOGIN_FORM, timeout=self.TIMEOUT)
        if res.status_code == 401:
            raise Exception("Invalid username or password")
        res.close()

        # check if we managed to login
        if 'CAUTH' not in s.cookies:
            raise Exception("Failed to authenticate as %s" % self.username)

        self.session = s

    def course_name_from_url(self, course_url):
        """Given the course URL, return the name, e.g., algo2012-p2"""
        return course_url.split('/')[3]

    def lecture_url_from_name(self, course_name):
        """Given the name of a course, return the video lecture url"""
        return self.LECTURE_URL % course_name

    # TODO: simple hack, something more elaborate needed
    def trim_path_part(self, s):
        mppl = self.max_path_part_len
        if mppl and len(s) > mppl:
            return s[:mppl]
        else:
            return s

    def get_response(self, url, retries=3, **kwargs):
        """
        Get the response
        """
        kwargs.update(timeout=self.TIMEOUT, allow_redirects=True)
        for i in range(retries):
            try:
                r = self.session.get(url, **kwargs)
                r.raise_for_status()
            except Exception as e:
                # print_("Warning: Retrying to connect url:%s" % url)
                pass
            else:
                return r
        raise e

    def get_headers(self, url):
        """
        Get the headers
        """
        r = self.get_response(url, stream=True)
        headers = r.headers
        r.close()
        return headers

    def get_page(self, url):
        """
        Get the content
        """
        r = self.get_response(url)
        page = r.content
        r.close()
        return page

    def get_json(self, url):
        """
        Get the json data
        """
        r = self.get_response(url)
        data = r.json()
        r.close()
        return data

    def get_json_get(self, url, get_data):
        """
        Get the json data
        """
        r = self.session.get(url, data=get_data)
        data = r.json()
        r.close()
        return data


def main():
    coursera = CourseraDownloader('tejasmehta0@gmail.com', 'gitajay')
    coursera.login('gamification-003')
    print coursera.get_page(coursera.lecture_url_from_name('gamification-003'))


if __name__ == '__main__':
    main()