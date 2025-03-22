from flask import Flask, request, render_template, redirect, url_for
import boto3
import os
import base64
from botocore.exceptions import ClientError

app = Flask(__name__)

# Initialize AWS clients with environment variables
rekognition = boto3.client(
    'rekognition',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'newawignbucket')

# Rest of your code remains the same...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))