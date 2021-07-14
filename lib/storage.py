import boto3
import os
import os.path
import json
from util import get_s3_client, get_bucket, is_local


class ObjectStorage(object):

  def __init__(self, bucket, client):
    self.bucket = bucket
    self.s3 = client
  
  @classmethod
  def create(klass, bucket):
    session = boto3.session.Session()
    client = session.client(
      service_name='s3',
      # endpoint_url='http://localhost:8006',
    )
    return klass(bucket, client)
  
  def put(self, key, file_or_data, meta={}):
    # @todo check
    data = file_or_data
    is_string = isinstance(file_or_data, basestring)
    print("Adding storage %s" % key)
    if is_string and os.path.exists(file_or_data):
      with open(file_or_data) as fh:
        data = fh.read()

    if not is_string:
      print("Dumping!")
      data = json.dumps(file_or_data)
    
    print(self.bucket)
    response = self.s3.put_object(Bucket=self.bucket, Body=data, ACL='private', Key=key, Metadata=meta)
    return response.get('ResponseMetadata', {}).get('HTTPStatusCode') not in [200, "200"]
  
  def get(self, key):
    response = self.s3.get_object(Bucket=self.bucket, Key=key)
    return response['Body'].read()

  def exists(self, key):
    try:
      self.s3.get_object(Bucket=self.bucket, Key=key)
      return True
    except:
      return False

  def remove(self, key):
    _response = self.s3.delete_object(
      Bucket=self.bucket,
      Key=key
    )



class LocalFiles(object):
    def __init__(self):
        self.root = '/home/zap/storage'
    
    def _fix_path(self, path):
        # @todo improve
        return os.path.join(self.root, path.replace('..', '.'))

    def exists(self, key_path):
      key_path = self._fix_path(key_path)
      return os.path.exists(key_path)

    def remove(self, key_path):
      key_path = self._fix_path(key_path)
      return os.remove(key_path)

    def get(self, path):
        data = {"meta": {}, "body": ""}
        with open(self._fix_path(path) as fh:
            data = json.loads(fh.read())
        return data.get("body")


    def put(self, key_path, contents, meta={}):
        key_path = self._fix_path(key_path)
        as_string = json.dumps({
            "meta": meta,
            "body": contents,
        })
        try:
          os.makedirs(os.path.dirname(key_path))
        except: pass

        with open(key_path, 'w') as fh:
          fh.write(data)
          return True

    @classmethod
    def create(klass):
        return klass()

def get_fs():
    if is_local():
        return LocalFiles()
    return ObjectStorage.create(get_bucket())