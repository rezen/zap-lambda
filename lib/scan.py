import os
import json
from datetime import datetime
import zap_common as z
from zapv2 import ZAPv2
from util import get_prefix
from target import Target

class ScanResults(object):
	def __init__(self, scanner, alerts, urls):
		self.scanner = scanner
		self.alerts = alerts
		self.urls = urls

	def get_alerts(self):
		all_alerts = []
		for alert_id in self.alerts:
			for alert in self.alerts[alert_id]:
				for key in ['description', 'solution', 'reference', 'name', 'other']:
					if key in alert:
						del alert[key]

				all_alerts.append(alert)
		return all_alerts

	def get_target(self):
		return self.scanner.get_target()

	def get_config(self):
		return self.scanner.config

	def as_dict(self):
		return {
			"scanner": self.scanner.as_dict(),
			"alerts": self.alerts,
			"urls": self.urls,
		}

class ResultsToStorage(object):

	def __init__(self, storage):
		self.storage = storage

	def save_alerts(self, alerts, key):
		report_data = "\n".join([json.dumps(a) for a in alerts])
		return self.storage.put_object(key, report_data)


	def save_results(self, results):
		target = results.get_target()
		now = datetime.today().strftime('%Y%m%d%H%I%s')
		alerts_key = "/".join([get_prefix(), "targets", target.slug(), "alerts", "%s.json" % now])
		self.save_alerts(results.get_alerts(), alerts_key)


class ScanConfig(object):

	def __init__(self, config={}):
		# @todo username/passwords stored securely
		self.timeout = int(os.environ.get("ZAP_TIMEOUT", 1))
		self.blacklist = ['-1', '50003', '60000', '60001']
		self.exclude = []
		self.spider = True
		self.technology = []
		self._valid_setters = [
			'timeout', 'blacklist', 
			'exclude', 'spider', 'technology'
		]
	

	def hash(self):
		pass

	def to_context(self):
		pass

	def as_dict(self):
		return {
			"timeout": self.timeout,
			"blacklist": self.blacklist,
		}

	def add_event(self, event):
		config = event.get('config', {})
		if 'config_file' in event:
			# @todo change to storage
			s3 = get_s3_client()
			obj = s3.get_object(Bucket=get_bucket(), Key=config_file)
			body = obj['Body']
			config = json.load(body.read())
		
		for key in config:
			if key in self._valid_setters:
				setattr(self, key, config[key])
		return event

	@classmethod
	def from_event(klass, event):
		if 'config_file' in event:
			return klass.from_s3(event['config_file'])
		obj = klass(event.get('config', {}))
		obj.target = Target.from_event(event)
		return obj

	@classmethod
	def for_target(klass, target):
		# zap-reports/https_example_com/config
		config_key =  "/".join([get_prefix(), target.slug(), "config"])
		obj = klass.from_s3(config_key)
		obj.target = Target
		return obj

	@classmethod
	def from_s3(klass, config_file):
		s3 = get_s3_client()
		obj = s3.get_object(Bucket=get_bucket(), Key=config_file)
		body = obj['Body']
		config = json.load(body.read())
		return klass(config)


class Scanner(object):
	
	version = "baseline-1.0"

	def __init__(self, config):
		self.config = config
		self.meta = {}
	
	def setup(self, z):
		config = self.config
		port = z.get_free_port()
		z.start_zap(port, ['-config', 'spider.maxDuration=2'])
		print("ZAP ON port %s" % port)

		zap = ZAPv2(proxies={'http': 'http://localhost:' + str(port), 'https': 'http://localhost:' + str(port)})
		z.wait_for_zap_start(zap, config.timeout * 60)
		self.meta['zap_version'] = zap.core.version
		return zap

	def run(self, zap, options={}):
		raise Exception("Not implemented")

	def teardown(self, zap):
		zap.core.delete_all_alerts()
		for site in zap.core.sites:
			zap.core.delete_site_node(site)
		zap.core.run_garbage_collection()
		zap.core.shutdown()

		print("Unlocked")

	def get_results(self):
		raise Exception("Not implemented")

	def get_target(self):
		return self.config.target

	def as_dict(self):
		return {
			"version": self.__class__.version,
			"config": config.as_dict(),
		}

	@classmethod
	def from_event(klass, event):
		return klass(target)

class BaselineScanner(Scanner):

	def run(self, zap, options={}):
		config = self.config
		target_url = config.target.url
		access = z.zap_access_target(zap, target_url)
		z.zap_spider(zap, target_url)
		z.zap_wait_for_passive_scan(zap, config.timeout * 60)

	def get_results(self, zap):
		config = self.config
		target_url = config.target.url
		alerts = z.zap_get_alerts(zap, target_url, config.blacklist, {})
		urls = zap.core.urls()
		return ScanResults(self, alerts, urls)


# @todo the scan manager should probably start ZAP
class ScanManager(object):

	def __init__(self, storage, lock, verifier):
			self.storage = storage
			self.lock = lock
			self.verifier = verifier

	def check_schedules(self):
		""" Go through the schedules queue up scans due to scan """
		pass

	def scans(self):
		""" What scans have run """
		return [

		]

	def scanners(self):
		""" What scanners are availble """
		return [
			BaselineScanner
		]
	
	def queue(self, config):
		""" Request to run a scan """
		can_scan, reason = self.can_scan_target(config)

		if not can_scan:
			return
		
		# @todo queue up event

	def can_scan_target(self, config):
		if self.is_already_scanning(config):
			return False, "Already scanning"
		
		return self.verifier.is_target_verified(config.get_target())

	def is_already_scanning(self, config):
		# Lock should be named based on target+config
		lock_name = config.get_target().slug()
		return self.locker.is_locked(lock_name)

	def scan(self, config):
		if not self.can_scan_target(config):
			return

		BaselineScanner(config)
		zap = scanner.setup(z)

		lock_name = config.get_target().slug()
		self.locker.lock(lock_name)

		try:
			print("Running scanner")
			scanner.run(zap)
			
			print("Getting results")
			results = scanner.get_results(zap)

			scanner.teardown(zap)
		except:
			pass

		self.locker.unlock(lock_name)


		save_to_s3 = ResultsToStorage(storage)
		save_to_s3.save_results(results)

		



