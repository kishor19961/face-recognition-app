from flask import Flask, request, render_template, redirect, url_for
import boto3
import os
import base64
from botocore.exceptions import ClientError
import io

# Create the application instance
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

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

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        print(f"Error rendering template: {str(e)}")
        return str(e), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        guard_id = request.form['guard_id']
        workforce_id = request.form['workforce_id']
        photo_data = request.form['photo']
        
        if not photo_data:
            return render_template('error.html', error="No photo provided")
        
        # Remove the data URL prefix to get just the base64 data
        if 'base64,' in photo_data:
            photo_data = photo_data.split('base64,')[1]
            
        # Decode base64 to bytes
        image_bytes = base64.b64decode(photo_data)
        
        try:
            # Search for similar faces in the S3 bucket
            response = rekognition.search_faces_by_image(
                CollectionId='facerecognition_collection',
                Image={
                    'Bytes': image_bytes
                },
                MaxFaces=1,
                FaceMatchThreshold=70
            )
            
            if response['FaceMatches']:
                match = True
                confidence = response['FaceMatches'][0]['Similarity']
                face_id = response['FaceMatches'][0]['Face']['FaceId']
                
                try:
                    # Get metadata and image from S3
                    s3_key = f"{face_id}.jpg"
                    metadata_response = s3.head_object(
                        Bucket=BUCKET_NAME,
                        Key=s3_key
                    )
                    metadata = metadata_response.get('Metadata', {})
                    
                    # Get the matched image from S3
                    s3_response = s3.get_object(
                        Bucket=BUCKET_NAME,
                        Key=s3_key
                    )
                    matched_image_bytes = s3_response['Body'].read()
                    matched_image_base64 = base64.b64encode(matched_image_bytes).decode('utf-8')
                    
                except ClientError as e:
                    metadata = {}
                    matched_image_base64 = None
            else:
                match = False
                confidence = 0
                metadata = {}
                matched_image_base64 = None
            
            return render_template('result.html',
                                match=match,
                                guard_id=guard_id,
                                workforce_id=workforce_id,
                                confidence=confidence,
                                metadata=metadata,
                                captured_image=photo_data,
                                matched_image=matched_image_base64)
                                
        except ClientError as e:
            return render_template('error.html', 
                                error=f"AWS Error: {str(e)}")
                                
    except Exception as e:
        return render_template('error.html',
                             error=f"Application Error: {str(e)}")

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
