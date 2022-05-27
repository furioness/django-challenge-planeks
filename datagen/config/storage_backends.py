# https://testdriven.io/blog/storing-django-static-and-media-files-on-amazon-s3/

from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = "static"
    default_acl = "public-read"


class PrivateMediaStorage(S3Boto3Storage):
    location = "private_media"
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
