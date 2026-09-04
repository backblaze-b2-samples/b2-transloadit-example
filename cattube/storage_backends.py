from botocore.config import Config
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class B2Storage(S3Boto3Storage):
    access_key = settings.B2_APPLICATION_KEY_ID
    secret_key = settings.B2_APPLICATION_KEY
    bucket_name = settings.B2_BUCKET_NAME
    endpoint_url = settings.B2_STORAGE_ENDPOINT_URL
    region_name = settings.B2_REGION
    custom_domain = settings.B2_PUBLIC_URL_CUSTOM_DOMAIN
    object_parameters = settings.B2_OBJECT_PARAMETERS
    config = Config(
        user_agent_extra='b2-transloadit-example (backblaze-b2-samples)',
    )


class StaticStorage(B2Storage):
    location = settings.B2_STATIC_LOCATION
