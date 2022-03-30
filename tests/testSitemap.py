import unittest
import json

import base64
import urllib
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import sitemap
from sitemap import Status

class TestLambda(unittest.TestCase):
    def setUp(self):
        sitemap.test = True

    def test_ping_event(self):
        with open('tests/fixtures/full_ping_event.json') as json_file:
            event = json.load(json_file)

            response = sitemap.update(event, None)

            self.assertEqual(getStatus(response), Status.MISSING_ACTION, msg="Unexpected status '{}'".format(getStatus(response)))

    def test_success(self):
        event = createEvent('tests/fixtures/success.json')

        response = sitemap.update(event, None)
        self.assertEqual(getStatus(response), Status.SUCCESS, msg="Unexpected status '{}'".format(getStatus(response)))

    def test_training(self):
        event = createEvent('tests/fixtures/training.json')

        response = sitemap.update(event, None)
        self.assertEqual(getStatus(response), Status.SUCCESS, msg="Unexpected status '{}'".format(getStatus(response)))

    def test_example(self):
        event = createEvent('tests/fixtures/github-webhook-example.json')

        response = sitemap.update(event, None)
        self.assertEqual(getStatus(response), Status.UNKNOWN_REPO, msg="Unexpected status '{}'".format(getStatus(response)))

    def test_wrong_workflow(self):
        event = createEvent('tests/fixtures/wrong-workflow.json')

        response = sitemap.update(event, None)
        self.assertEqual(getStatus(response), Status.WRONG_WORKFLOW, msg="Unexpected status '{}'".format(getStatus(response)))        

    def test_sitemap(self):
        (locs, lastmods) = sitemap.updateSitemap(sitemap.config["IIIF/website"])

        self.assertEqual(len(locs), len(lastmods), msg="Lenght of URLs should match the URLs")

        self.assertTrue("https://iiif.io/news/2022/02/02/Jisc-and-KB-join-consortium/" in locs,msg="Failed to find expected URL in list")

def getStatus(response):
    body = json.loads(response['body'])
    return Status.getStatus(body['status'])

def createEvent(body_path):
    with open('tests/fixtures/skeleton.json') as json_file:
        event = json.load(json_file)

        with open(body_path) as body_file:
            body = json.load(body_file)

            # URL encode then base64
            bodyEncoded = base64.b64encode(("payload=" + urllib.parse.quote_plus(json.dumps(body))).encode("utf-8")).decode("utf-8")
            event['body'] = bodyEncoded
            
            return event
        
if __name__ == '__main__':
    unittest.main()

