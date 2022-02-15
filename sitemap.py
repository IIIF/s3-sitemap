import json
import boto3
import pandas as pd
import base64
import urllib

config = {
    "IIIF/website": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "include": [".html" ]
    }
}

test = False

def updateSitemap(conf):
    s3client = boto3.client('s3')
    contents = s3client.list_objects_v2(Bucket=conf['s3'])
    log = ''

    locs = []
    lastmods = []
    for file in contents['Contents']:
        include = False
        for ext in conf['include']:
            if file['Key'].endswith(ext):
                include = True
                break
        if include:        
            locs.append(conf['url'] + file['Key'])
            lastmods.append(file['LastModified'].strftime("%Y-%m-%d"))
    
    df = pd.DataFrame({"loc": locs, "lastmod": lastmods})

    log += "Loading sitemap to: {}/sitemap.xml".format(conf['s3']) 

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

# we will get lots of updates at once... plus the sitemap itself...
def update(event, context):
    print (event)
    log = ""
    returnCode = 200
    payload = ''
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
                print (params.keys())
                log += "Failed to find payload parameter\n"
        else:    
            payload = json.loads(event['body'])

        if payload and 'action' in payload and payload['action'] == "completed":
            repoName = payload['repository']['full_name']
            if repoName in config and not test:
                log += updateSitemap(config[repoName])
            else:
                log += "Unknown repo: {}".format(repoName)
        else:
            log += "Event not completed\n"
            if 'action' not in payload:
                log += "No action field in message\n"
       
        print (log)
        print (json.dumps(payload, indent=4))
    except ValueError as error:
        log = "Failed to load body as JSON"
        print (log)
        print (event)

    body = {
        "message": log  
    }

    return {"statusCode": returnCode, "body": json.dumps(body)}
