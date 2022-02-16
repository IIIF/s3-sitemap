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

    def test_example(self):
        event = createEvent('tests/fixtures/github-webhook-example.json')

        response = sitemap.update(event, None)
        self.assertEqual(getStatus(response), Status.SUCCESS, msg="Unexpected status '{}'".format(getStatus(response)))


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

