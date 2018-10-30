from __future__ import print_function
import os
import sys
import json
from datetime import datetime
import hashlib
import traceback
import boto3

# Also PYTHONPATH
# https://joarleymoraes.com/hassle-free-python-lambda-deployment/
sys.path.append('vendor/')

try:
	import zap_common as z
	from zapv2 import ZAPv2
except Exception as err:
	print("[!] Could not import zap* libs")
	raise err

with open("/tmp/zap.out", 'a'):
    os.utime("/tmp/zap.out", None)


def get_bucket():
	return os.environ["AWS_BUCKET"]


def get_prefix():
	return os.environ.get("REPORT_PREFIX", "zap-reports")


def is_local():
	return os.environ.get("IS_LOCAL", False) in [1, "1", "true", "True"]


def get_s3_client():
	# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/clients.html
	if is_local():
		print("Configuring s3 client to use local")
		kwargs = {
			'service_name': 's3',
			'endpoint_url': 'http://localhost:8006',
		}
  		return boto3.resource(**kwargs).meta.client
  	else:
  		return boto3.client('s3')


class ScanConfig(object):
	def __init__(self, target):
		self.target = target
		self.timeout = int(os.environ.get("ZAP_TIMEOUT", 1))
		self.blacklist = ['-1', '50003', '60000', '60001']

	def is_already_scanning(self):
		return False

	def target_hash(self):
		md5 = hashlib.md5()
		md5.update(self.target)
		return md5.hexdigest()

	def as_dict(self):
		return {
			"timeout": self.timeout,
			"target": self.target,
			"blacklist": self.blacklist,
		}

	@staticmethod
	def is_valid_target(target):
		return target.startswith('http://') or target.startswith('https://')

	@classmethod
	def from_event(klass, event):
		if 'target' not in event:
			raise Exception("The event data does not include the target")

		target = event["target"]

		if not klass.is_valid_target(target):
			raise Exception("The target is not valid")
		return klass(target)

def run_scan(config):
	print("Getting free port")
	port = z.get_free_port()

	print("Starting zap")
	z.start_zap(port, ['-config', 'spider.maxDuration=2'])

	start = datetime.today().strftime('%Y%m%d%H%I%s')
	zap = ZAPv2(proxies={'http': 'http://localhost:' + str(port), 'https': 'http://localhost:' + str(port)})
	z.wait_for_zap_start(zap, config.timeout * 60)
	access = z.zap_access_target(zap, config.target)
	z.zap_spider(zap, config.target)
	z.zap_wait_for_passive_scan(zap, config.timeout * 60)
	alerts = z.zap_get_alerts(zap, config.target, config.blacklist, {})
	urls = zap.core.urls()

	# Cleanup alerts and remove nodes
 	zap.core.delete_all_alerts()
 	for site in zap.core.sites:
   		zap.core.delete_site_node(site)
   	zap.core.run_garbage_collection()
   	zap.core.shutdown()
 	
 	return {
 		"start": start,
 		"config": config.as_dict(),
 		"urls": urls,
	    "alerts": alerts,
 	}, zap

def handler(event, context):
	try:
		print("About to handle event")
		try:
			config = ScanConfig.from_event(event)
		except Exception as err:
			return {
				"success": False,
				"messages": [str(err)]
			}

		if config.is_already_scanning():
			return {
				"success": False,
				"messages": ["The target is already being currently scanned"]
			}

		print("About to run scan")
		report, zap = run_scan(config)
	 	
	 	print("Getting s3 client")
	 	s3 = get_s3_client()
	 	bucket = get_bucket()
	 	prefix = get_prefix()


	 	key = "%s/%s/%s.json" % (prefix, config.target_hash(), report['start'])
	 	meta = {
	        'target': config.target,
	        'zap_version': zap.core.version,
	 	}

		print("Saving report to s3")
	 	response = s3.put_object(Body=json.dumps(report), Bucket=bucket, Key=key, ACL='private', Metadata=meta)

	 	if response.get('ResponseMetadata', {}).get('HTTPStatusCode') not in [200, "200"]:
	 		return {
	 			"success": False,
	 			"messages": ["Could not save report to bucket %s" % bucket]
	 		}

		return {
		    "success": True,
		    "bucket": bucket,
		    "key": key,
		    "report": report,
		}
	except Exception as err:
		print("Error with handler")
		print(err)
		print(traceback.format_exc())


try:
	if is_local():
		print("Is local, creating test bucket")
		get_s3_client().create_bucket(Bucket=get_bucket())

		if len(sys.argv) > 1 and sys.argv[1] == '--test':
			print("Running local --test")
			print(handler({"target": "https://example.com"}, {}))

except Exception as err:
	print("Error with local setup")
	print(err)
	print(traceback.format_exc())