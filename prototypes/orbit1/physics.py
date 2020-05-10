from collections import namedtuple
import numpy
import pyrr

Planet = namedtuple('Planet', 'position, radius, mass')
Satellite = namedtuple('Satellite', 'position, prev_position, age')

def grav_accel(S: Satellite, P: Planet):
	d = P.position - S.position
	r = numpy.fmax(pyrr.vector.length(d), P.radius)
	return d * (P.mass/r**3)

def step(S: Satellite, P: Planet):
	return Satellite(2*S.position-S.prev_position+grav_accel(S,P), S.position, S.age+1)
