from django.conf import settings
from botocore.config import Config
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    access_key = settings.B2_APPLICATION_KEY_ID
    secret_key = settings.B2_APPLICATION_KEY
    bucket_name = settings.B2_BUCKET_NAME
    endpoint_url = f'https://s3.{settings.B2_REGION}.backblazeb2.com'
    region_name = settings.B2_REGION
    custom_domain = settings.B2_PUBLIC_URL_DOMAIN
    object_parameters = settings.B2_OBJECT_PARAMETERS
    location = settings.B2_STATIC_LOCATION
    config = Config(
        user_agent_extra='b2-transloadit-example (backblaze-b2-samples)',
    )
