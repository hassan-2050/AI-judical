from google.cloud import storage

def upload_to_gcs(bucket_name, file_stream, destination_blob_name, credentials_file):
    # Initialize the Google Cloud Storage client with the credentials
    storage_client = storage.Client.from_service_account_json(credentials_file)

    # Get the target bucket
    bucket = storage_client.bucket(bucket_name)

    # Upload the file to the bucket
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file_stream, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    print(f"File uploaded to gs://{bucket_name}/{destination_blob_name}")

    # Generate the URL for the uploaded file
    url = f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"

    return url
