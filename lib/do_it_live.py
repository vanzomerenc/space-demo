from collections import namedtuple
from pathlib import Path
from typing import List
import importlib
import inspect
import logging
import re

def LiveImports(*import_paths: List[str]):
	'''Reloads any of the listed modules when their files change.
	The listed modules must be local to the module calling LiveImports.
	'''
	
	caller = inspect.stack()[1]
	caller_globals = caller.frame.f_globals
	caller_name = caller_globals['__package__']
	
	logger = logging.getLogger(f'{__name__}-from-{caller_name}')
	logger.info(f'Starting live imports in {caller_name}.')
	logger.info(f'Packages that will be live-imported: {import_paths}')
	
	class ModuleInfo:
		def __init__(self, module):
			self.module = module
			self.fullname = self.module.__name__
			self.name = re.search(r'\w+$', self.fullname).group(0)
			self.last_mtime = self.get_mtime()
		
		def reload(self):
			self.module = importlib.reload(self.module)
			self.last_mtime = self.get_mtime()
		
		def get_mtime(self):
			return Path(self.module.__file__).stat().st_mtime
	
	modules = tuple(ModuleInfo(importlib.import_module(i, caller_name)) for i in import_paths)
	logger.info(f'Imported for the first time. Qualified names: {tuple(m.fullname for m in modules)}')
	
	def reimport():
		importlib.invalidate_caches()
		for m in modules:
			if m.get_mtime() > m.last_mtime:
				logger.info(f'Detected change in {m.fullname}. Reloading...')
				m.reload()
			caller_globals[m.name] = m.module
	
	reimport()
	return reimport
