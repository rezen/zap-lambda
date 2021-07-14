import re
import os
import uuid
from urlparse import urlparse
import hashlib

class Target(object):
	def __init__(self, full_url):
		parts = urlparse(full_url)
		self.url = full_url
		self.host = parts.hostname
		self.uuid = uuid.uuid3(uuid.NAMESPACE_URL, full_url)
		# @todo is_subdomain
	
	def slug(self):
		tmp_url = self.url.replace('.', '_').replace(':', '_')
 		return re.sub(r'\W+', '', tmp_url)

	def hash(self):
		md5 = hashlib.md5()
		md5.update(self.url)
		return md5.hexdigest()

	@staticmethod
	def is_valid_target(target):
		if target is None:
			return False
		return target.startswith('http://') or target.startswith('https://')

	@classmethod
	def from_event(klass, event):
		return klass.from_url(event['target'])

	@classmethod
	def from_url(klass, full_url):
		if Target.is_valid_target(full_url):
			return klass(full_url)
		raise Exception("Not a valid url - " + full_url)



class TargetVerifier(object):
	# Have targets in file or comma separated
	def __init__(self, valid_urls=[], s3=None):
		# look for is_verified in bucket
		self.verify_disabled = os.environ.get('DISABLE_VERIFY') in ['Y', '1', 'yes', 'y', 'true']
		self.valid_domains = os.environ.get('VERIFIED_DOMAINS', '').split(',')
		self.max_scans_per_hour = os.environ.get('MAX_HOURLY_SCANS', '8')


	def is_verified_domain(self, target):
		for domain in self.valid_domains:
			# @todo improve with proper url parsing
			if domain in target.url:
				return True
		return False

	def is_verified_site(self, target):
		return True

	def is_target_verified(self, target):
		if self.verify_disabled:
			return True, "Verification disabled"

		if self.is_verified_domain(target):
			return True, "Verified via domain"

		if self.is_verified_site(target):
			return True, "Verified via site"

		return False, "Target not a validated url"
