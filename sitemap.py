import json
import boto3
import pandas as pd

config = {
    "IIIF/website": {
        "s3": "iiif-website",
        "url": "https://iiif.io/",
        "include": [".html" ]
    }
}

def updateSitemap(conf):
    s3client = boto3.client('s3')
    contents = s3client.list_objects_v2(Bucket=conf['s3'])

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

    print()

# we will get lots of updates at once... plus the sitemap itself...
def update(event, context):
    log = ""
    payload = json.loads(event['body'])
    if payload['action'] == "completed":
        repoName = payload['repository']['full_name']
        if repoName in config:
            updateSitemap(config[repoName])
            log = payload
        else:
            log = "Unknown repo: {}".format(repoName)
    else:
        log = "Event not completed"

    body = {
        "message": log  
    }

    return {"statusCode": 200, "body": json.dumps(body)}
