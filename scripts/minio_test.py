import os
from minio import Minio

AWS_SERVER_PUBLIC_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SERVER_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

minioClient = Minio(
    endpoint="nrs.objectstore.gov.bc.ca",
    access_key=AWS_SERVER_PUBLIC_KEY,
    secret_key=AWS_SERVER_SECRET_KEY,
    region="US",
)

buckets = minioClient.list_buckets()
for buck in buckets:
    print(buck.name)
    objects2 = minioClient.list_objects_v2(bucket_name=buck.name, recursive=True)
    for ob in objects2:
        print(ob)

"""
objects1 = minioClient.list_objects(bucket_name='gdwuts',recursive=True)
for ob in objects1:
    print(ob)

objects2 = minioClient.list_objects_v2(bucket_name='gdwuts',recursive=True)
for ob in objects2:
    print(ob)
"""
