from flask import Flask, request, render_template, redirect, url_for
import boto3
import os
import base64
from botocore.exceptions import ClientError
import logging
import datetime

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
        current_datetime = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        current_user = 'kishor19961'
        return render_template('index.html',
                             current_datetime=current_datetime,
                             current_user=current_user)
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
            return render_template('result.html',
                                error_message="No photo provided",
                                guard_id=guard_id,
                                workforce_id=workforce_id)
        
        # Remove the data URL prefix to get just the base64 data
        if 'base64,' in photo_data:
            photo_data = photo_data.split('base64,')[1]
            
        # Decode base64 to bytes
        image_bytes = base64.b64decode(photo_data)
        
        try:
            # First, detect if there are any faces in the image
            detect_faces_response = rekognition.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['DEFAULT']
            )
            
            if not detect_faces_response['FaceDetails']:
                logger.info("No faces detected in the image")
                return render_template('result.html',
                                    match=False,
                                    guard_id=guard_id,
                                    workforce_id=workforce_id,
                                    captured_image=photo_data,
                                    error_message="No face detected in the image")
            
            # If faces are detected, proceed with face search
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
                
                try:
                    # List objects in the S3 bucket's index folder
                    response = s3.list_objects_v2(
                        Bucket=BUCKET_NAME,
                        Prefix='index/'
                    )
                    
                    s3_files = [item['Key'] for item in response.get('Contents', []) 
                              if not item['Key'].endswith('/')]
                    logger.info(f"Files in S3 bucket: {s3_files}")
                    
                    matched_image_base64 = None
                    metadata = {}
                    
                    # Try each file in S3
                    for s3_key in s3_files:
                        try:
                            # Get the image from S3
                            s3_response = s3.get_object(
                                Bucket=BUCKET_NAME,
                                Key=s3_key
                            )
                            image_bytes = s3_response['Body'].read()
                            
                            # Detect faces in this S3 image
                            detect_response = rekognition.detect_faces(
                                Image={
                                    'Bytes': image_bytes
                                },
                                Attributes=['DEFAULT']
                            )
                            
                            if detect_response['FaceDetails']:
                                # Search for faces in the collection that match this image
                                search_response = rekognition.search_faces_by_image(
                                    CollectionId='facerecognition_collection',
                                    Image={
                                        'Bytes': image_bytes
                                    },
                                    MaxFaces=1,
                                    FaceMatchThreshold=70
                                )
                                
                                if search_response['FaceMatches']:
                                    matched_face_id = search_response['FaceMatches'][0]['Face']['FaceId']
                                    
                                    # If this image contains our target face
                                    if matched_face_id == face_id:
                                        logger.info(f"Found matching image: {s3_key}")
                                        matched_image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                                        
                                        # Get metadata
                                        metadata_response = s3.head_object(
                                            Bucket=BUCKET_NAME,
                                            Key=s3_key
                                        )
                                        metadata = metadata_response.get('Metadata', {})
                                        metadata.update({
                                            'FileName': s3_key,
                                            'FaceId': face_id,
                                            'MatchConfidence': f"{confidence:.2f}%"
                                        })
                                        break
                            
                        except ClientError as e:
                            logger.error(f"Error processing {s3_key}: {str(e)}")
                            continue
                    
                except ClientError as e:
                    logger.error(f"Error accessing S3: {str(e)}")
                    metadata = {
                        'FaceId': face_id,
                        'Confidence': str(confidence),
                        'Note': 'Error accessing S3'
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
            error_message = "No face detected in the image" if "InvalidParameterException" in str(e) else str(e)
            return render_template('result.html',
                                match=False,
                                guard_id=guard_id,
                                workforce_id=workforce_id,
                                captured_image=photo_data,
                                error_message=error_message)
                                
    except Exception as e:
        logger.error(f"Application Error: {str(e)}")
        return render_template('result.html',
                             match=False,
                             guard_id=guard_id,
                             workforce_id=workforce_id,
                             error_message=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
