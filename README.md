# Create sitemap from s3

This lambda function will create a sitemap and store it in the root of the s3 bucket. It is initialised by using a GitHub web hook configured to point to the Lambda HTTP API end point.

## Configuration

In the `sitemap.py` file there is a config dict which maps the GitHub repository name to the URL and bucket

### Local development

You can invoke you the API by running:

```bash
serverless offline
```

and then run the test script:

```bash
./runTest.sh
```

