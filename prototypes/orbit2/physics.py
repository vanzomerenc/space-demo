from collections import namedtuple
from typing import List
import numpy
import pyrr

Scalar = float
Vector = pyrr.Vector3
ID = int

Particle = namedtuple('Particle', 'id, position, velocity, mass, radius')
Universe = List[Particle]

def update_position(particle: Particle, position: Vector) -> Particle:
	return Particle(particle.id, position, particle.velocity, particle.mass, particle.radius)

def update_velocity(particle: Particle, velocity: Vector) -> Particle:
	return Particle(particle.id, particle.position, velocity, particle.mass, particle.radius)


def grav_accel(particle: Particle, universe: Universe) -> Vector:
	A = 0 # Total acceleration times some constant.
	P = particle
	for U in universe:
		if U.id != P.id and U.mass > 0:
			_r_ = U.position - P.position
			r = pyrr.vector.length(_r_)
			A += (U.mass/(r*r*r))*_r_
	return A

def squared_grav_accel_gradient(particle: Particle, universe: Universe) -> Scalar:
	A = 0  # Total acceleration times some constant.
	VA = 0 # Divergence of total acceleration times some constant.
	P = particle
	for U in universe:
		if U.id != P.id and U.mass > 0:
			_r_ = U.position - P.position
			r = pyrr.vector.length(_r_)
			Va = U.mass/(r*r*r) # Divergence of single-interaction acceleration times some constant.
			VA += Va
			A += Va*_r_
	# Since we had to calculate acceleration anyway, it's nice to return it along with
	# the gradient.
	return (A, (4*VA)*A)



def step_verlet(universe: Universe, dt: Scalar) -> Universe:
	"""Verlet integration. It's great!
	Unfortunately, Verlet integration causes a noticeable precession when
	solving Kepler's problem unless the steps are very small.
	We're using it only for comparison.
	"""
	U = universe
	A0 = [grav_accel(p, U) for p in U]
	U = [update_position(p, p.position + dt*p.velocity + dt*dt*(1/2)*a0) for (p, a0) in zip(U, A0)]
	A1 = (grav_accel(p, U) for p in U)
	U = [update_velocity(p, p.velocity + dt*(1/2)*(a0 + a1)) for (p, a0, a1) in zip(U, A0, A1)]
	return U

def step_chin(universe: Universe, dt: Scalar) -> Universe:
	"""The 4th-order symplectic integration algorithm described in
	'Higher Order Force Gradient Symplectic Algorithms', by Chin and Kidwell (2000)
	https://arxiv.org/abs/physics/0006082v1
	
	The derivation of this algorithm, as well as its comparison to other numerical
	integration algorithms, is a bit beyond my mathematical literacy. In their paper,
	Chin and Kidwell provide a step-by-step outline of the algorithm.
	That outline is much appreciated.
	
	From my own observation, this algorithm does not handle absurdly large time steps
	very well; some orbits that merely precesses under Verlet integration will instead
	oscillate and then escape completely under Chin integration. My understanding is
	that symplectic integrators aren't usually supposed to do this, but what do I know.
	For reasonable time steps, though, Chin's algorithm will precess much less than
	Verlet's, without the runaway error that happens at large time steps.
	The only real downsides are that it requires computing the gradient of the squared
	force (or of the squared acceleration), which is not always trivial to do;
	it requires, in addition to the gradient computation, computing the force
	3 separate times, whereas Verlet integration only needs to calculate force once or
	twice depending on the exact method.
	"""
	U = universe # (r0, v0)
	U = [update_position(p, p.position + dt*(1/6)*p.velocity) for p in U]
	U = [update_velocity(p, p.velocity + dt*(3/8)*grav_accel(p, U)) for p in U]
	U = [update_position(p, p.position + dt*(1/3)*p.velocity) for p in U]
	VA2 = (squared_grav_accel_gradient(p, U) for p in U)
	U = [update_velocity(p, p.velocity + dt*(1/4)*(a + dt*dt*(1/48)*Va2)) for (p, (a, Va2)) in zip(U, VA2)]
	U = [update_position(p, p.position + dt*(1/3)*p.velocity) for p in U]
	U = [update_velocity(p, p.velocity + dt*(3/8)*grav_accel(p, U)) for p in U]
	U = [update_position(p, p.position + dt*(1/6)*p.velocity) for p in U]
	return U

step = step_chin
