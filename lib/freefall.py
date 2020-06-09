import abc
import numpy
import pyrr

from collections import namedtuple
from typing import Generic, List, NamedTuple, NewType


Scalar = float
Vector = pyrr.Vector3

# Why velocity and acceleration instead of momentum and force?
# Velocity can be used directly to calculate the next position,
# while momentum must first be multiplied by 1/mass.
# To calculate energy and resolve collisions, we do need to
# know the momentum, but this does not happen as often.
Time = NewType(int)
TimeSpan = Tuple[Time, Time]
Pos = NewType(Vector)
Vel = NewType(Vector)
Acc = NewType(Vector)
DAcc = NewType(Vector)

Layer = int
def Grouped(T):
	return Dict[Layer, List[T]]


# Why the split between FieldRule and Field?
# The idea is that FieldRule is completely stateless,
# and Field/FieldImpl add the bare minimum
# amount of state necessary to make things work together.

# Why is there a time parameter in the acceleration calculations?
# Because time-varying fields are a nice thing to have.

# Why is there no velocity parameter in acceleration calculations?
# Because I don't know what I'm doing and have no idea how to make
# sure the calculation would still be correct.
# I'll probably figure it out if I ever want to simulate magnetism
# or other relativistic effects.

class FieldRule(Generic[Emitter, Reactor]):
	"""A field applies acceleration to particles that interact with the field.
	"""
	@abstractmethod
	def acc(Eq: List[Pos], EQ: List[Emitter], Rq: Pos, RQ: Reactor, t: TimeSpan) -> Acc:
		"""Calculate acceleration for a single reactor based on its position and state.
		"""
	
	@abstractmethod
	def acc_div(Eq: List[Pos], EQ: List[Emitter], Rq: Pos, RQ: Reactor, t: TimeSpan) -> Tuple[Acc, DAcc]:
		"""Calculate acceleration and its divergence at the same time.
		Both of these are needed for some calculations, and it's often
		most efficient to calculate them both at the same time.
		"""


class FieldSolver(Generic[Field, Reactor]):
	

@dataclass
class Field:
	"""
	"""
	E: Layer
	R: Layer
	
	@abstractmethod
	def acc(Eq: List[Pos], Rq: List[Pos], t: TimeSpan) -> Sequence[Acc]:
		"""
		"""
	
	@abstractmethod
	def acc_div(Eq: List[Pos], Rq: List[Pos], t: TimeSpan) -> Sequence[Tuple[Acc, DAcc]]:
		"""
		"""


# To do: I'm expecting the most common case to be many reactors that each interact
# with a few small groups of emitters. Does it make sense to do a complete calculation
# for each reactor separately, and thereby save memory? Or to make things really
# predictable by doing calculations for each emitter group separately?
# Maybe something in the middle?
# This question is probably easily answered by profiling.

@dataclass
class FieldImpl(Field, Generic[Emitter, Reactor]):
	rule: FieldRule[Emitter, Reactor]
	EQ: List[Emitter]
	RQ: List[Reactor]
	
	def acc(Eq: List[Pos], Rq: List[Pos], t: TimeSpan) -> List[Acc]:
		return [rule.acc(Eq, EQ, rq, rQ, t) for rq, rQ in zip(Rq, RQ)]
	
	def acc_div(Eq: List[Pos], Rq: List[Pos], t: TimeSpan) -> List[Tuple[Acc, DAcc]]:
		return [rule.acc_div(Eq, EQ, rq, rQ, t) for rq, rQ in zip(Rq, RQ)]


@dataclass
class Integrator:
	"""
	"""
	# Each field is entered in here twice: once under its emitter layer,
	# and once under its reactor layer. So we can find them.
	EF: Grouped[Field]
	RF: Grouped[Field]
	
	# I am not sure if the comments in these functions make things any clearer,
	# but they at least help me remember what is going on.
	
	def _move_step(q: Grouped[Pos], p: Grouped[Vel], e1: Scalar) -> Grouped[Pos]:
		return {
			R: [               # per layer, a list of:
				qq + e1*pp         # new positions
				for qq, pp in zip( # per particle, from:
					p[R],              # a list of old positions, and
					q[R])]             # a list of velocities
			for R in q.keys()} # for all reactor layers.
	
	def _acc_step(q: Grouped[Pos], p: Grouped[Vel], t: TimeSpan, e1: Scalar) -> Grouped[Vel]:
		return {
			R: [                         # per layer, a list of:
				pp + e1*aa                   # new velocities
				for pp, aa in zip(           # per particle, from:
					p[FF.R],                     # a list of old velocities, and
					[                            # a list of accelerations, from:
						sum(a)                       # a sum of per-field accelerations
						for a in zip(*[              # per particle, from the same per field, from:
							F.acc(q[F.E], q[R], t)       # the state used to calculate the field
							for F in RF[R]]))]]          # per field affecting the layer
			for R in p.keys()}           # for all reactor layers.
	
	def _acc_div_step(q: Grouped[Pos], p: Grouped[Vel], t: TimeSpan, e1: Scalar, e2: Scalar) -> Grouped[Vel]:
		return {
			R: [                         # per layer, a list of:
				pp + e1*aa + 2*e2*aa*Daa     # new velocities
				for pp, aa, Daa in zip(      # per particle, from:
					p[FF.R],                     # a list of old velocities, and
					zip(*[                       # a list each of accelerations and divergences, from:
						(                            # (acceleration, divergence) tuples, from:
							sum([a for a, Da in aDa]),   # a sum of per-field accelerations, and
							sum([Da for a, Da in aDa]))  # a sum of per-field divergences
						for aDa in zip(*[            # per particle, from the same per field, from:
							F.acc_div(q[F.E], q[R], t)   # the state used to calculate the field
							for F in RF[R]]))])]         # per field affecting the layer
			for R in p.keys()}           # for all reactor layers.
	
	# To do: does it make sense to only provide a single time step for time-varying fields,
	# as we do here? What time steps should we be using? Should we try treating time
	# similarly to all the spatial coordinates?
	
	def step_verlet(q0: Grouped[Pos], p0: Grouped[Vel], t: TimeSpan) -> Tuple[Grouped[Pos], Grouped[Vel]]:
		"""Verlet integration. It's great!
		Unfortunately, Verlet integration causes a noticeable precession when
		solving Kepler's problem unless the steps are very small.
		We're using it only for comparison.
		"""
		dt = T[-1] - T[0]
		
		p1 =  _acc_step(q0, p0, t, (1/2)*dt)
		q1 = _move_step(q0, p1,          dt)
		p2 =  _acc_step(q1, p1, t, (1/2)*dt)
		return q1, p2
	
	def step_chin(q0: Grouped[Pos], p0: Grouped[Vel], t: TimeSpan) -> Tuple[Grouped[Pos], Grouped[Vel]]:
		"""The 4th-order symplectic integration algorithm described in
		'Higher Order Force Gradient Symplectic Algorithms', by Chin and Kidwell (2000)
		https://arxiv.org/abs/physics/0006082v1
		
		The derivation of this algorithm, as well as its comparison to other numerical
		integration algorithms, is a bit beyond my mathematical literacy. In their paper,
		Chin and Kidwell provide a step-by-step outline of the algorithm.
		That outline is much appreciated.
		
		Note that although this is a 4th-order algorithm, and so will almost always perform
		much better than Verlet's algorithm, it can in fact perform significantly worse
		for very fast / large time-step simulations. This is because the same properties
		that make it perform 10,000x better for a 10x smaller timestep will also make it
		perform, at best, 10,000x worse for a 10x larger timestep. This is true for all
		high-order integration algorithms, not just Chin's.
		"""
		dt = T[-1] - T[0]
		
		q1 =    _move_step(q0, p0,    (1/6)*dt)
		p1 =     _acc_step(q1, p0, t, (3/8)*dt)
		q2 =    _move_step(q1, p1,    (1/3)*dt)
		p2 = _acc_div_step(q2, p1, t, (1/4)*dt, (1/192)*dt*dt)
		q3 =    _move_step(q2, p2,    (1/3)*dt)
		p3 =     _acc_step(q3, p2, t, (3/8)*dt)
		q4 =    _move_step(q3, p3,    (1/6)*dt)
		return q4, p3
