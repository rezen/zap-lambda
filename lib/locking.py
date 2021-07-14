import re

# @todo have elasticcache option
class LockViaStorage(object):
	def __init__(self, storage):
		self.storage = storage
	
	def setup(self):
		pass

	def _name_to_key(self, key):
		return "_locks/" + re.sub(r'\W+', '', key) + ".lock"

	def lock(self, name):
		# https://stackoverflow.com/questions/14969273/s3-object-expiration-using-boto
		if self.is_locked(name):
			return
		
		name = self._name_to_key(name)
		self.storage.put(name, '')

	def unlock(self, name):
		name = self._name_to_key(name)
		self.storage.remove(name)

	def is_locked(self, name):
		name = self._name_to_key(name)
		try:
			return self.storage.exists(name)
		except Exception as err: # @todo get right error to catch
			print("is-locked", err)
			return False
		return True
	