### How to use a Python script to perform URL Sharing from Object Storage

This will output a pre-signed URL for your object that will allow the user to download it for a pre-determined length of time.

1. Create an .env file that contains the following information:
    - *OBJSTOR_PUBLIC_ENDPOINT = 'https://nrs.objectstore.gov.bc.ca:443'*
    - *AWS_SERVER_PUBLIC_KEY = 'YOUR_OBJECT_STORAGE_USER_ID'*
    - *AWS_SERVER_SECRET_KEY = 'YOUR_OBJECT_STORAGE_SECRET_KEY'*
3. Download **requirements.txt, constants.py** and **create_presigned_url_for_s3_objects.py** from this Object Storage GitHub repo
4. Save all 4 files in the same folder
5. Open your code editor of choice (our team uses Visual Studio Code) and point your directory to the folder with those files
6. Open a cmd terminal and run *pip install -r requirements.txt* to install the python packages needed to run scripts from our GitHub repo.
7. Open **create_presigned_url_for_s3_objects.py** and change the variable for bucketname to your bucket name. Save your changes.
8. Next, run *python create_presigned_url_for_s3_objects.py -o \<object> -t \<time>*
    - **Example:** create_presigned_url_for_s3_objects.py -o test.txt -t 3600

**SECURITY CONSIDERATIONS**
  
What are requestors of your pre-signed URLs allowed access to – everything, or are some areas restricted? In the case of restrictions, the Object Storage User ID used in the .env file should have a bucket policy applied that grants access only to what a requestor would be allowed to download from your bucket. [Our team](mailto:nrids.optimize@gov.bc.ca) can set this up by request through the Object Storage Admin Dashboard.\
The command-line variable value for “expiration” is counted in seconds. It is strongly recommended that you keep the expiration times short to ensure users can use only the current signed URLs and not ones signed in the past.
