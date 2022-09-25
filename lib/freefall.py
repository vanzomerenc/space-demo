# Character palette for non-ASCII characters used in this file, with ASCII replacements in parentheses.
# ᵢⱼₖ (ijk): implied loop indices, as Unicode subscripts to try to be more readable.
# ∇ (D): gradient of a scalar or divergence of a vector.

import abc
import numpy
import pyrr

from collections import namedtuple
from typing import Any, Generic, List, NamedTuple, NewType


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
DAcc = NewType(Scalar)

Layer = NewType(str)
Property = NewType(str)


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
	
	@property
	@abstractmethod
	def E(self) -> Property:
		"""The name of the property of the emitters of this field that affects
		the field interaction.
		"""
	
	@property
	@abstractmethod
	def R(self) -> Property:
		"""The name of the property of the reactors to this field that affects
		the field interaction.
		"""
	
	@abstractmethod
	def acc(self, Eq: List[Pos], EQ: List[Emitter], Rq: Pos, RQ: Reactor, t: TimeSpan) -> Acc:
		"""Calculate acceleration applied by a layer of emitters to a single reactor.
		"""
	
	@abstractmethod
	def acc_div(self, Eq: List[Pos], EQ: List[Emitter], Rq: Pos, RQ: Reactor, t: TimeSpan) -> Tuple[Acc, DAcc]:
		"""Calculate acceleration and its divergence at the same time.
		Both of these are needed for some calculations, and it's often
		most efficient to calculate them both at the same time.
		"""


# To do: I'm expecting the most common case to be many reactors that each interact
# with a few small groups of emitters. Does it make sense to do a complete calculation
# for each reactor separately, and thereby save memory? Or to make things really
# predictable by doing calculations for each field rule separately?
# Maybe something in the middle?
# This question is probably easily answered by profiling.


@dataclass
class Integrator:
	"""
	"""
	
	
	def _move_step(self,
			q: Dict[Layer, List[Pos]],
			p: Dict[Layer, List[Vel]],
			e1: Scalar
			) -> Dict[Layer, List[Pos]]:
		return {
			R: [qᵢ + e1*pᵢ for qᵢ, pᵢ in zip(q[R], p[R])]
			for R in q.keys()}
	
	def _acc_step(self,
			q: Dict[Layer, List[Pos]],
			p: Dict[Layer, List[Vel]],
			Q: Dict[Tuple[Property, Layer], List[Any]],
			F: Dict[Layer, List[Tuple[FieldRule, Layer]]],
			t: TimeSpan,
			e1: Scalar
			) -> Dict[Layer, List[Vel]]:
		return {
			R: [
				pᵢ + e1*sum(
					Fⱼ.acc(q[Eⱼ], Q[Fⱼ.E, Eⱼ], qᵢ, Qᵢⱼ, t)
					for Qᵢⱼ, Fⱼ, Eⱼ in zip(Qᵢ, *F[R]))
				for qᵢ, pᵢ, Qᵢ in zip(q[R], p[R], zip(*(Q[Fⱼ.R, R] for Fⱼ, Eⱼ in F[R])))]
			for R in p.keys()}
	
	def _acc_div_step(self,
			q: Dict[Layer, List[Pos]],
			p: Dict[Layer, List[Vel]],
			Q: Dict[Tuple[Property, Layer], List[Any]],
			F: Dict[Layer, List[Tuple[FieldRule, Layer]]],
			t: TimeSpan,
			e1: Scalar,
			e2: Scalar
			) -> Dict[Layer, List[Vel]]:
		return {
			R: [
				pᵢ + e1*aᵢ + e2*2*∇aᵢ*aᵢ
				for pᵢ, aᵢ, ∇aᵢ in (
					# This ends up iterating over a∇aᵢ twice, which is inefficient.
					# It's been left the way it is for the sake of clarity.
					(pᵢ, sum(aᵢⱼ for aᵢⱼ, ∇aᵢⱼ in a∇aᵢ), sum(∇aᵢⱼ for aᵢⱼ, ∇aᵢⱼ in a∇aᵢ))
					for pᵢ, a∇aᵢ in (
						pᵢ,
						(
							Fⱼ.div_acc(q[Eⱼ], Q[Fⱼ.E, Eⱼ], qᵢ, Qᵢⱼ, t)
							for Qᵢⱼ, Fⱼ, Eⱼ in zip(Qᵢ, *F[R]))
						for qᵢ, pᵢ, Qᵢ in zip(q[R], p[R], zip(*(Q[Fⱼ.R, R] for Fⱼ, Eⱼ in F[R])))))]
			for R in p.keys()}
	
	
	# To do: does it make sense to only provide a single time step for time-varying fields,
	# as we do here? What time steps should we be using? Should we try treating time
	# similarly to all the spatial coordinates?
	
	def step_verlet(self,
			q0: Dict[Layer, List[Pos]],
			p0: Dict[Layer, List[Vel]],
			Q: Dict[Tuple[Property, Layer], List[Any]],
			F: Dict[Layer, List[Tuple[FieldRule, Layer]]],
			t: TimeSpan
			) -> Tuple[Dict[Layer, List[Pos]], Dict[Layer, List[Vel]]]:
		"""Verlet integration. It's great!
		Unfortunately, Verlet integration causes a noticeable precession when
		solving Kepler's problem unless the steps are very small.
		We're using it only for comparison.
		"""
		dt = T[-1] - T[0]
		
		p1 = self. _acc_step(q0, p0, Q, F, t, (1/2)*dt)
		q1 = self._move_step(q0, p1,                dt)
		p2 = self. _acc_step(q1, p1, Q, F, t, (1/2)*dt)
		return q1, p2
	
	def step_chin(self,
			q0: Dict[Layer, List[Pos]],
			p0: Dict[Layer, List[Vel]],
			Q: Dict[Tuple[Property, Layer], List[Any]],
			F: Dict[Layer, List[Tuple[FieldRule, Layer]]],
			t: TimeSpan
			) -> Tuple[Dict[Layer, List[Pos]], Dict[Layer, List[Vel]]]:
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
		
		q1 = self.   _move_step(q0, p0,          (1/6)*dt)
		p1 = self.    _acc_step(q1, p0, Q, F, t, (3/8)*dt)
		q2 = self.   _move_step(q1, p1,          (1/3)*dt)
		p2 = self._acc_div_step(q2, p1, Q, F, t, (1/4)*dt, (1/192)*dt*dt)
		q3 = self.   _move_step(q2, p2,          (1/3)*dt)
		p3 = self.    _acc_step(q3, p2, Q, F, t, (3/8)*dt)
		q4 = self.   _move_step(q3, p3,          (1/6)*dt)
		return q4, p3




Mass = NewType(Scalar)

class GravityFieldRule(FieldRule[Mass, None]):
	"""An example rule for Newtonian gravity
	"""
	
	@abstractmethod
	def acc(self, Eq: Pos, EQ: Mass, Rq: Pos, RQ: None, t: TimeSpan) -> Acc:
		a = 0
		for Eqᵢ, EQᵢ in zip(Eq, EQ):
			if Eq == Rq or EQ == 0:
				continue
			_rᵢ_ = Eqᵢ - Rq
			rᵢ = pyrr.vector.length(_rᵢ_)
			a += (EQᵢ/(rᵢ*rᵢ*rᵢ))*_rᵢ_
		return a
	
	@abstractmethod
	def acc_div(self, Eq: Pos, EQ: Mass, Rq: Pos, RQ: None, t: TimeSpan) -> Tuple[Acc, DAcc]:
		a = 0
		∇a = 0
		for Eqᵢ, EQᵢ in zip(Eq, EQ):
			if Eq == Rq or EQ == 0:
				continue
			_rᵢ_ = Eqᵢ - Rq
			rᵢ = pyrr.vector.length(_rᵢ_)
			∇aᵢ = EQᵢ/(rᵢ*rᵢ*rᵢ)
			∇a += ∇aᵢ
			a += ∇aᵢ*_rᵢ_
		return a, 2*∇a


# In the future, particle and interaction IDs will probably be int.
# Since this is a prototype where we don't care about
# performance, str is a bit more convenient.
Particle = NewType(str)
Field = NewType(str)

@dataclass
class Universe:
	"""
	"""
	_n: Dict[Layer, List[Particle]]                 # Particle names
	_q: Dict[Layer, List[Pos]]                      # Particle positions
	_p: Dict[Layer, List[Vel]]                      # Particle velocities
	_Q: Dict[Layer, Dict[Property, List[Any]]]      # Particle properties
	_R: Dict[Layer, Set[Field]]                     # Fields that particles react to
	_E: Dict[Layer, Set[Field]]                     # Fields that particles emit
	_F: Dict[Field, Tuple[Layer, Layer, FieldRule]] # The layers and rule for each field
	
	def create_layer(self, properties: Set[Property]) -> Layer:
		L = ID()
		self._n[L] = list()
		self._q[L] = list()
		self._p[L] = list()
		self._Q[L] = {p: list() for p in properties}
		self._R[L] = set()
		self._E[L] = set()
		return L
	
	def destroy_layer(self, layer: Layer) -> None:
		L = layer
		del self._n[L]
		del self._q[L]
		del self._p[L]
		del self._Q[L]
		for Fᵢ in self._R[L]:
			del self.F[Fᵢ]
		del self._R[L]
		for Fᵢ in self._E[L]:
			del self.F[Fᵢ]
		del self._E[L]
	
	def create_field(self, reactor: Layer, rule: FieldRule, emitter: Layer) -> Field:
		F = ID()
		self._R[reactor].add(F)
		self._E[emitter].add(F)
		self._F[F] = reactor, rule, emitter
		return F
	
	def destroy_field(self, field: Field) -> None:
		F = field
		R, _, E = self._F[F]
		self._R[R].remove(F)
		self._E[E].remove(F)
		del self._F[F]
	
	def create_particle(self,
			layer: Layer,
			position: Pos,
			velocity: Vel,
			charges: Dict[Property, Any],
			) -> Particle
		pass
	
	def destroy_particle(self, particle: Particle) -> None:
		pass
	
	def get_position(self, particle: Particle) -> Pos:
		pass
	
	def get_velocity(self, particle: Particle) -> Vel:
		pass
	
	def get_charge(self, particle: Particle, charge: Property) -> Any:
		pass
	+
