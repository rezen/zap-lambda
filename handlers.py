from __future__ import print_function
import os
import sys
sys.path.append('vendor/')
import time
import traceback
from lib.target import TargetVerifier
from lib.scan import ScanConfig, ScanManager
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

def on_scan_requested(event, context):
	if 'target' not in event:
		raise Exception("The event data does not include the target")

	config = ScanConfig.from_event(event)
	storage = get_fs()
	lock = LockViaStorage(storage)
	verifier = TargetVerifier()
	manager = ScanManager(storage, lock, verifier)
	result, error = manager.scan(config)
	return result


def on_target_verified(event, context):
	pass
	# @todo 

def on_scan_complete(event, context):
	pass