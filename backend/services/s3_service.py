import os
import time
import boto3
import pandas as pd
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

max_retries = 5


def _get_aws_credentials(creds_by_excel=False):
    access_key = os.environ['S3_CLIENT_ID']
    secret_key = os.environ['S3_SECRET_KEY']

    if creds_by_excel:
        credentials_dir = os.environ.get('CREDENTIALS_DIR', '')
        credentials = pd.read_excel(credentials_dir)
        access_key = credentials.loc[credentials['application'] == 'aws_access_key', 'username'].values[0]
        secret_key = credentials.loc[credentials['application'] == 'aws_secret_key', 'username'].values[0]
    
    return access_key, secret_key


def connect_s3(return_type='client', region_name='ap-southeast-5'):
    if region_name is None:
        region_name = os.environ.get('S3_BUCKET_REGION', 'ap-southeast-5')
    access_key, secret_key = _get_aws_credentials()

    if return_type == 'client':
        for i in range(max_retries):
            try:
                return boto3.client(
                    service_name='s3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region_name,
                )
            except Exception as e:
                if i < max_retries - 1:
                    print(f'[Attempt {i+1}] Failed to connect to AWS S3. Retrying...')
                    time.sleep(5)
                else:
                    print(f'Max attempts reached. Error:\n{e}')
                    return None

    elif return_type == 'resource':
        for i in range(max_retries):
            try:
                return boto3.resource(
                    's3',
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region_name,
                )
            except Exception as e:
                if i < max_retries - 1:
                    print(f'[Attempt {i+1}] Failed to create S3 resource. Retrying...')
                    time.sleep(5)
                else:
                    print(f'Max attempts reached. Error:\n{e}')
                    return None
    else:
        raise ValueError("return_type must be 'client' or 'resource'")


def s3_upload_image(item_path, username):
    s3_client = connect_s3(return_type='client')
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3_key = f"{username}/{item_path}"
    temp_dir = os.path.join(os.path.dirname(__file__), '..', 'tempImages')

    for i in range(max_retries):
        try:
            s3_client.upload_file(
                Filename=os.path.join(temp_dir, item_path),
                Bucket=bucket_name,
                Key=s3_key,
            )
            return True
        except Exception as e:
            if i < max_retries - 1:
                print(f'[Attempt {i+1}] Image upload failed. Retrying...')
            else:
                print('Max S3 upload attempts reached.')
                raise e


def s3_delete_image(s3_key):
    s3_client = connect_s3(return_type='client')
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


def s3_get_presigned_urls_for_user(username, item_ids):
    """Generate presigned URLs for a list of item IDs belonging to a user."""
    bucket_name = os.environ['S3_BUCKET_NAME']
    s3_resource = connect_s3('resource')
    s3_client = connect_s3('client')
    bucket = s3_resource.Bucket(bucket_name)

    user_image_keys = [obj.key for obj in bucket.objects.filter(Prefix=username)]

    results = []
    for item_id in item_ids:
        matched_key = None
        for k in user_image_keys:
            if item_id in k:
                matched_key = k
                break

        if matched_key:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': matched_key},
                ExpiresIn=3600,
            )
            results.append({'id': item_id, 'url': url, 's3_key': matched_key})

    return results
