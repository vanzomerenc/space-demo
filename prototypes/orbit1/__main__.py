from math import log, ceil, floor
from pathlib import Path
import pyrr
import moderngl
import moderngl_window
from .physics import *


class Universe:
	def __init__(self):
		self.P = Planet(pyrr.Vector3([0,0,0]), 0.1, 0.0001)
		self.S = [Satellite(pyrr.Vector3([-0.023,1.033,0]), pyrr.Vector3([-0.017,1.027,0]), 1)]
		
	def step(self):
		self.S.append(step(self.S[-1], self.P))
		decay_rate = 1.03
		bits = ceil(log(self.S[-1].age, decay_rate))
		for i in range(0, bits):
			while i < len(self.S) and self.S[-1].age - self.S[i].age > decay_rate**(bits-i):
				del self.S[i]
		
		


class Orbit1Prototype(moderngl_window.WindowConfig):
	title = "Testing..."
	resource_dir = (Path(__file__).parent/'resources').resolve()

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.camera = moderngl_window.scene.camera.KeyboardCamera(self.wnd.keys, aspect_ratio=self.wnd.aspect_ratio)
		self.camera_enabled = False
		self.prog = self.load_program('cube_simple.glsl')
		self.prog['color'].value = 1.0, 1.0, 1.0, 1.0
		self.universe = Universe()
		self.planet = moderngl_window.geometry.sphere(radius=self.universe.P.radius)
		self.satellite = moderngl_window.geometry.sphere(radius=0.1)
		self.old_sat = moderngl_window.geometry.quad_2d(size=(0.01, 0.01))

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
		self.ctx.enable_only(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
		
		self.universe.step()

		self.prog['m_proj'].write(self.camera.projection.matrix)
		self.prog['m_camera'].write(self.camera.matrix)
		
		self.prog['m_model'].write(pyrr.Matrix44.from_translation((self.universe.S[-1].position.x, self.universe.S[-1].position.y, -3.5), dtype='f4'))
		self.satellite.render(self.prog)
		
		
		for s in self.universe.S:
			self.prog['m_model'].write(pyrr.Matrix44.from_translation((s.position.x, s.position.y, -3.5), dtype='f4'))
			self.old_sat.render(self.prog)
		
		self.prog['m_model'].write(pyrr.Matrix44.from_translation((self.universe.P.position.x, self.universe.P.position.y, -3.5), dtype='f4'))
		
		self.planet.render(self.prog)



if __name__ == '__main__':
	print('Testing...')
	moderngl_window.run_window_config(Orbit1Prototype)
