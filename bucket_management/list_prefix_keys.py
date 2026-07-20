# scripts/list_prefix_keys.py
import os, sys
from botocore.config import Config
import boto3
from datetime import timezone

def load_dotenv_if_present():
    # Try DOTENV_PATH -> CWD\.env -> script_dir\.env
    candidates = []
    dotenv_path = os.environ.get('DOTENV_PATH')
    if dotenv_path:
        candidates.append(os.path.expanduser(os.path.expandvars(dotenv_path)))
    candidates.append(os.path.join(os.getcwd(), '.env'))
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(script_dir, '.env'))
    except Exception:
        pass
    for cand in candidates:
        if cand and os.path.isfile(cand):
            try:
                with open(cand, 'r', encoding='utf-8') as f:
                    for line in f:
                        s = line.strip()
                        if not s or s.startswith('#') or '=' not in s:
                            continue
                        k, v = s.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
                break
            except Exception as e:
                print(f"Warning: could not read .env '{cand}': {e}", file=sys.stderr)

def req(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        print(f"Missing required env var: {name}", file=sys.stderr)
        sys.exit(1)
    return v

def main():
    load_dotenv_if_present()

    endpoint = req('S3_ENDPOINT')
    bucket   = req('S3_BUCKET_NAME')
    access   = req('ACCESS_KEY')
    secret   = req('SECRET_KEY')
    prefix   = os.environ.get('S3_BUCKET_PREFIX','')
    region   = os.environ.get('ECS_REGION','').strip() or None

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access,
        aws_secret_access_key=secret,
        config=Config(signature_version='s3v4', s3={'addressing_style':'path'})
    )

    # List keys under the prefix (up to 200)
    print(f"\nListing keys under prefix: {repr(prefix)}\n")
    keys = []
    token = None
    while True:
        kwargs = dict(Bucket=bucket, Prefix=prefix, MaxKeys=200)
        if token:
            kwargs['ContinuationToken'] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get('Contents', []):
            keys.append(obj['Key'])
        if resp.get('IsTruncated'):
            token = resp.get('NextContinuationToken')
        else:
            break

    if not keys:
        print("No objects found under this prefix.")
        return

    for i, k in enumerate(keys, 1):
        print(f"{i:2d}. {repr(k)}")

if __name__ == '__main__':
    main()