from __future__ import print_function
import os
import sys
# https://joarleymoraes.com/hassle-free-python-lambda-deployment/
sys.path.append('vendor/')

import json
import time
import traceback
from lib.util import is_local, get_s3_client, get_bucket, dump_s3
from lib.target import Target, TargetVerifier
from lib.scan import ScanConfig, BaselineScanner, ResultsToStorage
from lib.locking import LockViaStorage
from lib.storage import get_fs

try:
	import zap_common as z
	from zapv2 import ZAPv2
except Exception as err:
	print("[!] Could not import zap* libs")
	raise err

with open("/tmp/zap.out", 'a'):
    os.utime("/tmp/zap.out", None)


def handler(event, context):
	if 'target' not in event:
		raise Exception("The event data does not include the target")

	s3 = get_s3_client()
	bucket = get_bucket()
	target = Target.from_event(event)
	config = ScanConfig.from_event(event)
	config.target = target
	storage = get_fs()
	lock = LockViaStorage(storage)
	verifier = TargetVerifier()
	scanner = BaselineScanner(lock, verifier, config)

	can_scan, reason = scanner.can_scan_target()
	if not can_scan:
		return {
			"success": can_scan,
			"message": reason,
		}

	print("Verified due to " + reason)
	try:
		print("Setting up scanner")
		zap = scanner.setup(z)		
		print("Running scanner")
		scanner.run(zap)
		
		print("Getting results")
		results = scanner.get_results(zap)
		# @todo emit event for each result
		scanner.teardown(zap)
		save_to_s3 = ResultsToStorage(storage)
		save_to_s3.save_results(results)

		return {
			"success": True,
			"message": "Scanner has completed",
			"data": {
				"target": target.slug(),
				"alerts": results.get_alerts(),
			},
		}

	except Exception as err:
		print("Error with handler")
		print(err)
		print(traceback.format_exc())


try:
	if is_local():
		os.environ['VERIFIED_DOMAINS'] = "example.com"
		print("Is local, creating test bucket")
		time.sleep(6)
		get_s3_client().create_bucket(Bucket=get_bucket())

		if len(sys.argv) > 1 and sys.argv[1] == '--test':
			print("Running local --test")
			data = handler({"target": "https://example.com/", "config": {}}, {})
			print(json.dumps(data, indent=2))
			dump_s3()

		exit(0)

except Exception as err:
	print("Error with local setup")
	print(err)
	print(traceback.format_exc())
	exit(1)