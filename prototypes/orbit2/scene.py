from math import pi
import sys
import pyrr
from . import physics

def V(x,y,z):
	return pyrr.Vector3([x,y,z])

universe = [
	physics.Particle(0, V(0,0,0), V(0,0,0), 4*pi**2, 0.1), # A sun
	physics.Particle(1, V(0,1,0), V(-2*pi,0,0), 4*pi**2 / 500, 0.01), # A planet
	physics.Particle(2, V(0, 1.03, 0), V(-2*pi*1.25, 0, 0), 4*pi**2 / 500 / 25, 0.005), # A moon
	physics.Particle(3, V(0.5*3**0.5, 0.5, 0), V(-pi, pi*3**0.5, 0)*1.01, 0, 0.0025), # Satellite at a Lagrange point
	physics.Particle(4, V(-0.5*3**0.5, 0.5, 0), V(-pi, -pi*3**0.5, 0)*1.01, 0, 0.0025), # Another Lagrange satellite
	physics.Particle(5, V(0, -1.01, 0), V(2*pi/1.01, 0, 0), 0, 0.0025), # Horseshoe orbit (unstable)
]
