from flask import Flask, request, render_template, redirect, url_for
import boto3
import os
import base64
from botocore.exceptions import ClientError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application instance
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

# Initialize AWS clients with environment variables
def get_aws_credentials():
    return {
        'aws_access_key_id': os.environ.get('AWS_ACCESS_KEY_ID'),
        'aws_secret_access_key': os.environ.get('AWS_SECRET_ACCESS_KEY'),
        'region_name': os.environ.get('AWS_REGION', 'us-east-1')
    }

rekognition = boto3.client('rekognition', **get_aws_credentials())
s3 = boto3.client('s3', **get_aws_credentials())

BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'newawignbucket')

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return str(e), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        guard_id = request.form['guard_id']
        workforce_id = request.form['workforce_id']
        photo_data = request.form['photo']
        
        logger.info(f"Received upload request for Guard ID: {guard_id}, Workforce ID: {workforce_id}")
        
        if not photo_data:
            logger.error("No photo data received")
            return render_template('error.html', error="No photo provided")
        
        # Remove the data URL prefix to get just the base64 data
        if 'base64,' in photo_data:
            photo_data = photo_data.split('base64,')[1]
            
        # Decode base64 to bytes
        image_bytes = base64.b64decode(photo_data)
        
        try:
            # Search for similar faces in the S3 bucket
            logger.info("Searching for similar faces...")
            response = rekognition.search_faces_by_image(
                CollectionId='facerecognition_collection',
                Image={
                    'Bytes': image_bytes
                },
                MaxFaces=1,
                FaceMatchThreshold=70
            )
            
            logger.info(f"Rekognition response: {response}")
            
            if response['FaceMatches']:
                match = True
                confidence = response['FaceMatches'][0]['Similarity']
                face_id = response['FaceMatches'][0]['Face']['FaceId']
                external_image_id = response['FaceMatches'][0]['Face']['ExternalImageId']
                logger.info(f"Match found! Face ID: {face_id}, External Image ID: {external_image_id}, Confidence: {confidence}")
                
                try:
                    # Try different possible S3 keys based on the actual structure
                    possible_keys = [
                        f"index/{external_image_id}.jpg",        # index/Darshan1.jpg
                        f"index/{external_image_id}.jpg.jpg",    # index/Darshan1.jpg.jpg
                        f"index/{external_image_id}",            # index/Darshan1
                        f"{external_image_id}.jpg",              # Darshan1.jpg
                        f"{external_image_id}.jpg.jpg"           # Darshan1.jpg.jpg
                    ]
                    
                    matched_image_base64 = None
                    metadata = {}
                    
                    for s3_key in possible_keys:
                        try:
                            logger.info(f"Trying to retrieve image with key: {s3_key}")
                            # Get metadata and image
                            metadata_response = s3.head_object(
                                Bucket=BUCKET_NAME,
                                Key=s3_key
                            )
                            metadata = metadata_response.get('Metadata', {})
                            
                            # If metadata exists, get the image
                            s3_response = s3.get_object(
                                Bucket=BUCKET_NAME,
                                Key=s3_key
                            )
                            matched_image_bytes = s3_response['Body'].read()
                            matched_image_base64 = base64.b64encode(matched_image_bytes).decode('utf-8')
                            logger.info(f"Successfully retrieved image and metadata with key: {s3_key}")
                            break
                        except ClientError as e:
                            logger.info(f"Key {s3_key} not found, trying next...")
                            continue
                    
                    # Add face information to metadata
                    metadata.update({
                        'FaceId': face_id,
                        'ExternalImageId': external_image_id,
                        'Confidence': str(confidence),
                        'MatchConfidence': f"{confidence:.2f}%"
                    })
                        
                except ClientError as e:
                    logger.error(f"Error accessing S3: {str(e)}")
                    metadata = {
                        'FaceId': face_id,
                        'ExternalImageId': external_image_id,
                        'Confidence': str(confidence),
                        'Note': 'Original image not found in S3'
                    }
                    matched_image_base64 = None
            else:
                logger.info("No match found")
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
            logger.error(f"AWS Error: {str(e)}")
            return render_template('error.html', 
                                error=f"AWS Error: {str(e)}")
                                
    except Exception as e:
        logger.error(f"Application Error: {str(e)}")
        return render_template('error.html',
                             error=f"Application Error: {str(e)}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
