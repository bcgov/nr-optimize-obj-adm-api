import s3
import yaml
import subprocess
from ....storage.error import StorageError

with open('s3.yaml', 'r') as fi:
    config = yaml.load(fi)

connection = s3.S3Connection(**config['s3'])
storage = s3.Storage(connection)
# Then you call methods on the Storage instance.

# The following code creates a bucket called “com-prometheus-my-bucket” and asserts the bucket exists. Then it deletes the bucket, and asserts the bucket does not exist.

my_bucket_name = 'com-prometheus-my-bucket'
storage.bucket_create(my_bucket_name)
assert storage.bucket_exists(my_bucket_name)
storage.bucket_delete(my_bucket_name)
assert not storage.bucket_exists(my_bucket_name)
# The following code lists all the buckets and all the keys in each bucket.

for bucket in storage.bucket_list():
    print(bucket.name, bucket.creation_date)
    for key in storage.bucket_list_keys(bucket.name):
        print('\\t', key.key, key.size, key.last_modified, key.owner.display_name)

# The following code uses the default bucket and uploads a file named “example” from the local filesystem
# as “example-in-s3” in s3. It then checks that “example-in-s3” exists in storage, downloads the file as
# “example-from-s3”, compares the original with the downloaded copy to ensure they are the same, deletes
# “example-in-s3”, and finally checks that it is no longer in storage.

try:
    storage.write("example", "example-in-s3")
    exists, metadata = storage.exists("example-in-s3")
    assert exists
    metadata = storage.read("example-in-s3", "example-from-s3")
    assert 0 == subprocess.call(['diff', "example", "example-from-s3"])
    storage.delete("example-in-s3")
    exists, metadata = storage.exists("example-in-s3")
    assert not exists
except StorageError as e:
    print('failed:', e)

# The following code again uploads “example” as “example-in-s3”. This time it uses the bucket “my-other-bucket” explicitly,
# and it sets some metadata and checks that the metadata is set correctly. Then it changes the metadata and checks that as well.

headers = {
    'x-amz-meta-state': 'unprocessed',
    }
remote_name = s3.S3Name("example-in-s3", bucket="my-other-bucket")
try:
    storage.write("example", remote_name, headers=headers)
    exists, metadata = storage.exists(remote_name)
    assert exists
    assert metadata == headers
    headers['x-amz-meta-state'] = 'processed'
    storage.update_metadata(remote_name, headers)
    metadata = storage.read(remote_name, "example-from-s3")
    assert metadata == headers
except StorageError as e:
    print('failed:', e)

# The following code configures “com-prometheus-my-bucket” with a policy that restricts “myuser” to write-only.
# myuser can write files but cannot read them back, delete them, or even list them.

storage.bucket_set_policy("com-prometheus-my-bucket", data={
        "Version": "2008-10-17",
        "Id": "BucketUploadNoDelete",
        "Statement": [
                {
                    "Sid": "Stmt01",
                    "Effect": "Allow",
                    "Principal": {
                            "AWS": "arn:aws:iam::123456789012:user/myuser"
                            },
                    "Action": [
                            "s3:AbortMultipartUpload",
                            "s3:ListMultipartUploadParts",
                            "s3:PutObject",
                            ],
                    "Resource": [
                            "arn:aws:s3:::com-prometheus-my-bucket/*",
                            "arn:aws:s3:::com-prometheus-my-bucket"
                            ]
                    }
                ]
        })
