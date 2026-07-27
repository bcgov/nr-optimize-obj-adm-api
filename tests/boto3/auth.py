from boto3_helpers.auth import get_client, get_resource
from tests.constants import ACCESS_KEY, SECRET_KEY

def test_get_client():
    try: 
        new_client = get_client(access_key=ACCESS_KEY, secret_key=SECRET_KEY)
    except Exception as e:
        print(f"Error occurred: {e}")
        new_client = None
    assert new_client is not None
    return new_client

    
def test_get_resource():
    try: 
        new_resource = get_resource(access_key=ACCESS_KEY, secret_key=SECRET_KEY)
    except Exception as e:
        print(f"Error occurred: {e}")
        new_resource = None
    assert new_resource is not None
    return new_resource


test_get_client()
test_get_resource()