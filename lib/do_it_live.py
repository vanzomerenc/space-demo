from pathlib import Path
from typing import List
import importlib
import inspect
import logging

def LiveImports(imported: List[str]):
	'''Reloads any of the listed modules when their files change.
	The listed modules must be local to the module calling LiveImports.
	'''
	logger = logging.getLogger(__name__)
	frameinfo = inspect.stack()[1]
	file_name = frameinfo.filename
	package_name = frameinfo.frame.f_globals['__package__']
	globals_dict = frameinfo.frame.f_globals
	
	logger.info(f'Starting live imports in {package_name} ({file_name}).')
	logger.info(f'Packages that will be live-imported: {imported}')
	
	timestamps = dict()
	def reimport():
		importlib.invalidate_caches()
		for m in imported:
			mtime = (Path(file_name).parent/(m+'.py')).stat().st_mtime
			if m in timestamps:
				if timestamps[m] < mtime:
					logger.info(f'Detected change in {m}. Reloading...')
					globals_dict[m] = importlib.reload(globals_dict[m])
			else:
				globals_dict[m] = importlib.import_module(package_name+'.'+m)
			timestamps[m] = mtime
	
	reimport()
	return reimport
