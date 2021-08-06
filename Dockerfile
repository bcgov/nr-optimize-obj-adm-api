FROM docker-remote.artifacts.developer.gov.bc.ca/alpine:3.14
WORKDIR /src
COPY ["send-s3bucket_watermarks.py", "./"]
RUN apk add --no-cache python3 py3-pip
ENTRYPOINT ["python3", "send-s3bucket_watermarks.py"]