import importlib
from math import log, ceil, floor, pi
from pathlib import Path
import pyrr
import moderngl
import moderngl_window

__live_imports__timestamps = dict()
def live_imports():
	importlib.invalidate_caches()
	for m in [
		'physics',
		'scene',
		]:
		mtime = (Path(__file__).parent/(m+'.py')).stat().st_mtime
		if m in __live_imports__timestamps:
			if __live_imports__timestamps[m] < mtime:
				print('Detected change in '+m+'. Reloading...')
				globals()[m] = importlib.reload(globals()[m])
		else:
			globals()[m] = importlib.import_module(__package__+'.'+m)
		__live_imports__timestamps[m] = mtime

live_imports()

class Orbit2Prototype(moderngl_window.WindowConfig):
	title = "Testing..."
	resource_dir = (Path(__file__).parent).resolve()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.camera = moderngl_window.scene.camera.KeyboardCamera(self.wnd.keys, aspect_ratio=self.wnd.aspect_ratio)
		self.camera_enabled = False
		self.prog = self.load_program('render.glsl')
		self.sprite = moderngl_window.geometry.sphere(radius=1.0)

	def key_event(self, key, action, modifiers):
		keys = self.wnd.keys

		if self.camera_enabled:
			self.camera.key_input(key, action, modifiers)

		if action == keys.ACTION_PRESS:
			if key == keys.C:
				self.camera_enabled = not self.camera_enabled
				self.wnd.mouse_exclusivity = self.camera_enabled
				self.wnd.cursor = not self.camera_enabled


	def mouse_position_event(self, x: int, y: int, dx, dy):
		if self.camera_enabled:
			self.camera.rot_state(-dx, -dy)


	def resize(self, width: int, height: int):
		self.camera.projection.update(aspect_ratio=self.wnd.aspect_ratio)


	def render(self, time: float, frametime: float):
		
		live_imports()
		
		self.ctx.enable_only(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
		
		scene.universe = physics.step(scene.universe, 1/3600)
		
	
		self.prog['m_proj'].write(self.camera.projection.matrix)
		self.prog['m_camera'].write(self.camera.matrix)
		
		self.prog['color'].value = 1.0, 1.0, 1.0, 1.0
		for p in scene.universe:
			self.prog['m_model'].write(
				pyrr.matrix44.multiply(
					pyrr.Matrix44.from_scale((p.radius, p.radius, p.radius), dtype='f4'),
				pyrr.matrix44.multiply(
					pyrr.Matrix44.from_translation((p.position.x, p.position.y, -2.5), dtype='f4'),
					pyrr.Matrix44.from_scale((10, 10, 10), dtype='f4'),
					)))
			self.sprite.render(self.prog)



if __name__ == '__main__':
	print('Testing...')
	moderngl_window.run_window_config(Orbit2Prototype)
