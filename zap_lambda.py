import os
import sys
import json

# Also PYTHONPATH
# https://joarleymoraes.com/hassle-free-python-lambda-deployment/
sys.path.append('vendor/')

try:
	import zap_common as z
except Error as err:
	print("[!] Could not import zap_common")
	raise err

try:
	from zapv2 import ZAPv2
except Error as err:
	print("[!] Could not import zapv2")
	raise err


with open("/tmp/zap.out", 'a'):
    os.utime("/tmp/zap.out", None)

zap_ip = 'localhost'
port = 8080
timeout = 1
blacklist = ['-1', '50003', '60000', '60001']

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

	zap = ZAPv2(proxies={'http': 'http://' + zap_ip + ':' + str(port), 'https': 'http://' + zap_ip + ':' + str(port)})
	z.wait_for_zap_start(zap, timeout * 60)
	access = z.zap_access_target(zap, target)
	z.zap_spider(zap, target)
	z.zap_wait_for_passive_scan(zap, timeout * 60)
	alerts = z.zap_get_alerts(zap, target, blacklist, {})
	urls = zap.core.urls()
	zap.core.shutdown()

	return {
	    "success": True,
	    "urls": urls,
	    "alerts": alerts,
	}
