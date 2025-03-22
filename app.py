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
        
        # Save the image temporarily
        photo_path = os.path.join('static', 'captured_photo.jpg')
        with open(photo_path, 'wb') as f:
            f.write(image_bytes)
        
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
            
            # Clean up the temporary file
            os.remove(photo_path)
            
            return render_template('result.html',
                                match=match,
                                guard_id=guard_id,
                                workforce_id=workforce_id,
                                confidence=confidence,
                                metadata=metadata,
                                captured_image=photo_data)
                                
        except ClientError as e:
            return render_template('error.html', 
                                error=f"AWS Error: {str(e)}")
                                
    except Exception as e:
        return render_template('error.html',
                             error=f"Application Error: {str(e)}")
