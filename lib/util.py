import os
import boto3

def dump_s3():
	data = get_s3_client().list_objects(Bucket=get_bucket())
	for item in data.get('Contents', []):
		print(" - " + item['Key'])


def get_bucket():
	return os.environ["AWS_BUCKET"]

def get_prefix():
	return os.environ.get("REPORT_PREFIX", "zap-reports")

def is_local():
	return os.environ.get("IS_LOCAL", False) in [1, "1", "true", "True"]

def get_lambda_timeout():
	return int(os.environ.get("LAMBDA_TIMEOUT", 1))

def get_s3_client():
	# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
	if is_local():
		print("Configuring s3 client to use local")
		kwargs = {
			'service_name': 's3',
			'endpoint_url': 'http://localhost:4572',
		}
  		return boto3.resource(**kwargs).meta.client
  	else:
  		return boto3.client('s3')

