import os
import sys
import json
from datetime import datetime
import hashlib
import boto3

# Also PYTHONPATH
# https://joarleymoraes.com/hassle-free-python-lambda-deployment/
sys.path.append('vendor/')

try:
	import zap_common as z
except Exception as err:
	print("[!] Could not import zap_common")
	raise err

try:
	from zapv2 import ZAPv2
except Exception as err:
	print("[!] Could not import zapv2")
	raise err


with open("/tmp/zap.out", 'a'):
    os.utime("/tmp/zap.out", None)

bucket = os.environ["AWS_BUCKET"]
zap_ip = 'localhost'
port = z.get_free_port()
timeout = os.environ.get("ZAP_TIMEOUT ", 1)
blacklist = ['-1', '50003', '60000', '60001']
s3 = boto3.client('s3')

z.start_zap(port, ['-config', 'spider.maxDuration=2'])

def handler(event, context):
	if 'target' not in event: 
		return {
			"success": False,
			"messages": ["The context was missing target"]
		}

	target = event["target"]

	if not (target.startswith('http://') or target.startswith('https://')):
		return {
			"success": False,
			"messages": ["The target did not look like a url"]
		}

	start = datetime.today().strftime('%Y%m%d%H%I%s')
	md5 = hashlib.md5()
	md5.update(target)

	zap = ZAPv2(proxies={'http': 'http://' + zap_ip + ':' + str(port), 'https': 'http://' + zap_ip + ':' + str(port)})
	z.wait_for_zap_start(zap, timeout * 60)
	access = z.zap_access_target(zap, target)
	z.zap_spider(zap, target)
	z.zap_wait_for_passive_scan(zap, timeout * 60)
	alerts = z.zap_get_alerts(zap, target, blacklist, {})
	urls = zap.core.urls()

	# Cleanup alerts and remove nodes
 	zap.core.delete_all_alerts()
 	for site in zap.core.sites:
   		zap.core.delete_site_node(site)
   	zap.core.run_garbage_collection()
 	
 	data = {
 		"urls": urls,
	    "alerts": alerts,
 	}

 	# Coming soon!
 	# s3.put_object(Body=json.dumps(data), Bucket=bucket, Key=key)

 	key = "zap/%s/%s.json" % (md5.hexdigest(), start)

	return {
	    "success": True,
	    "bucket": bucket,
	    "key": key,
	    "data": data,
	}
