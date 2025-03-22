from flask import Flask, request, render_template, redirect, url_for
import boto3
import os
import base64
from botocore.exceptions import ClientError

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
        photo = request.files['photo']
        
        if not photo:
            return render_template('error.html', error="No photo provided")
            
        # Save the uploaded file temporarily
        photo_path = os.path.join('static', 'captured_photo.jpg')
        photo.save(photo_path)
        
        # Read the image file
        with open(photo_path, 'rb') as image_file:
            image_bytes = image_file.read()
        
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
                    metadata_response = s3.head_object(
                        Bucket=BUCKET_NAME,
                        Key=f"{face_id}.jpg"
                    )
                    metadata = metadata_response.get('Metadata', {})
                except ClientError:
                    metadata = {}
            else:
                match = False
                confidence = 0
                metadata = {}
            
            # Convert the captured image to base64 for display
            with open(photo_path, 'rb') as image_file:
                encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Clean up the temporary file
            os.remove(photo_path)
            
            return render_template('result.html',
                                match=match,
                                guard_id=guard_id,
                                workforce_id=workforce_id,
                                confidence=confidence,
                                metadata=metadata,
                                captured_image=encoded_image)
                                
        except ClientError as e:
            return render_template('error.html', 
                                error=f"AWS Error: {str(e)}")
                                
    except Exception as e:
        return render_template('error.html',
                             error=f"Application Error: {str(e)}")
