import unittest

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import sitemap
from bs4 import BeautifulSoup

class TestLambda(unittest.TestCase):
    def setUp(self):
        sitemap.test = True

    def test_redirect(self):
        with open('tests/fixtures/html/redirect.html') as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            host = 'https://example.com'

            url = sitemap.checkURL(soup, host, '/tests/fixtures/html/redirect.html')

            self.assertEqual(url, host + '/get-started/why-iiif/', msg="Expected a different URL got '{}'".format(url))

    def test_noredirect(self):
        filename = 'tests/fixtures/html/normal.html'
        with open(filename) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            host = 'https://example.com'

            url = sitemap.checkURL(soup, host, filename)

            self.assertEqual(url, host + filename, msg="Expected a different URL got '{}'".format(url))

    def test_conical(self):
        filename = 'tests/fixtures/html/broken.html'
        with open(filename) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            host = 'https://example.com'

            url = sitemap.checkURL(soup, host, filename)

            self.assertEqual(url, 'https://iiif.io/api/cookbook/recipe/0028-sequence-range-partial-canvases/', msg="Expected a different URL got '{}'".format(url))

if __name__ == '__main__':
    unittest.main()
