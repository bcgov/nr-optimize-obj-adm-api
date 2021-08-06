FROM docker-remote.artifacts.developer.gov.bc.ca/alpine:3.14
WORKDIR /src
COPY ["ministry-billing-report/send_s3bucket_watermarks.py", "./"]
RUN apk add --no-cache python3 py3-pip
ENTRYPOINT ["python3", "send_s3bucket_watermarks.py"]