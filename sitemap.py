import json
import boto3
import pandas as pd
import base64
import urllib
import re
from enum import Enum
from html.parser import HTMLParser
from bs4 import BeautifulSoup

config = {
    "IIIF/website": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "workflow": ".github/workflows/live.yml",
        "include": [".html" ]
    },
    "IIIF/api": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "workflow": ".github/workflows/live.yml",
        "include": [".html" ]
    },
    "IIIF/cookbook-recipes": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "workflow": ".github/workflows/live.yml",
        "include": [".html" ]
    },
    "IIIF/guides": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "workflow": ".github/workflows/live.yml",
        "include": [".html" ]
    },
    "IIIF/training": {
        "s3": "training.iiif.io",
        "url": "https://training.iiif.io/",
        "workflow": ".github/workflows/master.yml",
        "include": [".html" ]
    }
}

test = False

def constructURL(host, path):
    if host.endswith('/'):
        host = host[:-1]
    if not path.startswith('/'):
        path = "/" + path

    return host + path        

def canonicalElements(soup):
    links = soup.find_all("link")

    for link in links:
        if link.has_attr('rel') and link.get("rel")[0] == "canonical":
            return link.get("href")
    return None         

def checkURL(soup, host, path):    
    location = constructURL(host, path)
    canonical = canonicalElements(soup)
    if canonical:
        if 'http' in canonical:
            location = canonical
        else:
            location = constructURL(host, canonical)

    return location

def updateSitemap(conf):
    s3client = boto3.client('s3')
    log = ''

    locations = {}
    contents = s3client.list_objects_v2(Bucket=conf['s3'])
    while True:
        for file in contents['Contents']:
            include = False
            for ext in conf['include']:
                if file['Key'].endswith(ext):
                    include = True
                    break
            if include:        
                location = constructURL(conf['url'], file['Key'])
                if file['Key'].endswith('.html'):
                    # check to see if this is a redirect html page
                    soup = BeautifulSoup(s3client.get_object(Bucket=conf['s3'], Key=file['Key'])['Body'].read().decode('utf-8'), 'html.parser')
                    location = checkURL(soup, conf['url'], file['Key'])

                if location not in locations:
                    locations[location] = file['LastModified'].strftime("%Y-%m-%d")
                else:
                    print ('Found duplicate: {} from {}'.format(location,  constructURL(conf['url'], file['Key'])))

        if contents['IsTruncated']:
            contents = s3client.list_objects_v2(Bucket=conf['s3'], ContinuationToken=contents['NextContinuationToken'])
        else:
            break
    
    locs = []
    lastmods = []
    for location in locations:
        locs.append(location)
        lastmods.append(locations[location])
                
    df = pd.DataFrame({"loc": locs, "lastmod": lastmods})

    log += "Loading sitemap to: {}/sitemap.xml".format(conf['s3']) 

    if not test:
        s3client.put_object(
                    ACL='public-read',
                    Bucket=conf['s3'],
                    Body=(bytes(df.to_xml(
                                namespaces={"":"http://www.sitemaps.org/schemas/sitemap/0.9"},
                                index=False,
                                root_name='urlset',
                                row_name='url').encode('UTF-8'))),
                    ContentType="application/xml; charset=UTF-8", 
                    CacheControl="no-cache, no-store",
                    Key = 'sitemap.xml'
        )

        return log
    else:
        return (locs, lastmods)

# we will get lots of updates at once... plus the sitemap itself...
def update(event, context):
    #if not test:
    #    print (event)
    log = ""
    returnCode = 200
    payload = ''
    status = Status.INITAL
    try:
        if 'isBase64Encoded' in event and event['isBase64Encoded']:
            params = urllib.parse.parse_qs(base64.b64decode(event['body']).decode('utf-8'), encoding='utf-8')
            if 'payload' in params:
                try:
                    payload = json.loads(params['payload'][0])
                except ValueError as error:
                    log += 'Failed to load payload due to \n'
                    log += str(error) + '\n'
                    log += params['payload'][0] + "\n"

            else:
                log += "Failed to find payload parameter\n"
                print (params.keys())
        else:    
            payload = json.loads(event['body'])

        if payload:
            if 'action' in payload:
                if payload['action'] == "completed":
                    repoName = payload['repository']['full_name']
                    if repoName in config: 
                        if 'workflow' in payload and 'path' in payload['workflow']:
                            if payload['workflow']['path'] == config[repoName]['workflow']:
                                status = Status.SUCCESS
                                if not test:
                                    log += updateSitemap(config[repoName])
                            else:       
                                status = Status.WRONG_WORKFLOW
                                log += "This event is for workflow {} ({}) and I want {}".format(payload['workflow']['name'], payload['workflow']['path'], config[repoName]['workflow'])
                        else:
                            status = Status.WRONG_WORKFLOW
                            log += "This event doesn't have the required workflow fields set"
                    else:
                        status = Status.UNKNOWN_REPO
                        log += "Unknown repo: {}".format(repoName)
                else:        
                    status = Status.ACTION_NOT_COMPLETED
            else: 
                status = Status.MISSING_ACTION
        else:
            status = Status.MISSING_PAYLOAD
            log += "Event not completed\n"
            if 'action' not in payload:
                log += "No action field in message\n"
       
        if not test:
            print (log)
            print (status.value)
        #    print (json.dumps(payload, indent=4))
    except ValueError as error:
        log = "Failed to load body as JSON"
        print (log)
        print (event)

    body = {
        "message": log,
        "status": status
    }

    return {"statusCode": returnCode, "body": json.dumps(body)}

class Status(str, Enum):
    INITAL = "inital"
    MISSING_PAYLOAD = "Payload parameter not set in POST body"
    UNKNOWN_REPO = "Recieved event from Repo that isn't configured"
    ACTION_NOT_COMPLETED = "Workflow action not completed"
    MISSING_ACTION = "Action missing"
    SUCCESS = "Successfully updated sitemap"
    WRONG_WORKFLOW = "Event is for the wrong workflow"

    def getStatus(status_message):
        for item in Status:
            if status_message == item.value:
                return item
