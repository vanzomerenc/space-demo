from collections import namedtuple
import numpy
import pyrr

Planet = namedtuple('Planet', 'position, radius, mass')
#Satellite = namedtuple('Satellite', 'position, prev_position, age')
Satellite = namedtuple('Satellite', 'position, velocity, age')

def grav_accel(S: Satellite, P: Planet):
	d = P.position - S.position
	r = pyrr.vector.length(d)#numpy.fmax(pyrr.vector.length(d), P.radius)
	return d * (P.mass/r**3)

def squared_grav_accel_gradient(S: Satellite, P: Planet):
	d = P.position - S.position
	r = pyrr.vector.length(d)#numpy.fmax(pyrr.vector.length(d), P.radius)
	return d * (4*P.mass**2/r**6)

def step_position_verlet(S: Satellite, P: Planet):
	"""If I was going to have a favorite numerical integration algorithm,
	this would be it. It's very simple, reasonably accurate (though not
	amazingly accurate by any stretch), plays well with external constraints
	because there's no velocity term to keep track of, and it's symplectic to boot.
	I'm not entirely sure what "symplectic" means other than that it preserves
	energy and is time-reversible. It sounds cool.
	
	Unfortunately, Verlet integration causes a noticeable precession when
	solving the Kepler problem unless the steps are very small.
	"""
	return Satellite(2*S.position-S.prev_position+grav_accel(S,P), S.position, S.age+1)

def step_verlet(S: Satellite, P: Planet):
	"""This is a more conventional variant of Verlet integration,
	so it can be compared with other integrators that aren't as easy
	to express without an explicit velocity term.
	"""
	q0 = S.position
	S0 = Satellite(q0, None, None)
	p0 = S.velocity
	q1 = q0 + p0 + 1/2*grav_accel(S0,P)
	S1 = Satellite(q1, None, None)
	p1 = p0 + 1/2*(grav_accel(S0,P)+grav_accel(S1,P))
	return Satellite(q1, p1, S.age+1)

def step_chin(S: Satellite, P: Planet):
	"""The 4th-order symplectic integration algorithm described in
	'Higher Order Force Gradient Symplectic Algorithms', by Chin and Kidwell (2000)
	https://arxiv.org/abs/physics/0006082v1
	
	The derivation of this algorithm, as well as its comparison to other numerical
	integration algorithms, is a bit beyond my mathematical literacy. In their paper,
	Chin and Kidwell provide a step-by-step outline of the algorithm that's basically
	what's listed in the code below. That outline is much appreciated.
	
	From my own observation, this algorithm does not handle absurdly large time steps
	very well; some orbits that merely precesses under Verlet integration will instead
	oscillate and then escape completely under Chin's integration. My understanding is
	that symplectic integrators aren't usually supposed to do this, but what do I know.
	For reasonable time steps, though, Chin's algorithm will precess much less than
	Verlet, without the runaway error that happens at large time steps.
	The only real downsides are that it requires computing the gradient of the squared
	force (or of the squared acceleration), which is not always trivial to do;
	it requires, in addition to the gradient computation, computing the force
	3 separate times, whereas Verlet integration only needs to calculate force once or
	twice depending on the exact method; and it isn't as simple to add constraints
	(adding constraints to position-Verlet integration is embarassingly simple).
	"""
	q0 = S.position
	p0 = S.velocity
	q1 = q0 + 1/6*p0
	S1 = Satellite(q1, None, None)
	p1 = p0 + 3/8*grav_accel(S1,P)
	q2 = q1 + 1/3*p1
	S2 = Satellite(q2, None, None)
	p2 = p1 + 1/4*(grav_accel(S2,P)+1/48*squared_grav_accel_gradient(S2,P))
	q3 = q2 + 1/3*p2
	S3 = Satellite(q3, None, None)
	p3 = p2 + 3/8*grav_accel(S3,P)
	q4 = q3 + 1/6*p3
	return Satellite(q4, p3, S.age+1)
