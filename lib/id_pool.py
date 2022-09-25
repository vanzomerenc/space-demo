

class id_pool:
	"""etc etc
	
	There are two groups of items: alive, and dead, which
	each form a contiguous span in the pool.
	
	Removing items from the pool "shuffles" the order of
	the items to place the removed items in the dead span.
	Adding items sorts the pool to move items from the dead
	span to the live span.
	
	This is not a true shuffle. It isn't really random, and
	we restrict it so that each item can only be swapped with
	another item once. If we need to swap an item more than once,
	we must undo the existing swap. This has the effect that
	swapped items always point at each other.
	
	Since the items in each swapped pair point to each other,
	we can find any item in the pool via a single constant-time
	lookup. Adding or removing a single item is also constant-time.
	Iteration over the live items is trivial and optimal (as long as
	we do not care about order) because the live items are contiguous.
	"""
	
	def __init__(self):
		self._order = list()
		self._count = 0
	
	def add(self) -> (int, int):
		"""
		The result of this function is the sort performed
		while adding a new item.
		The first value in the result is the location where
		the new value was added, and the second value is the
		location that the existing value at that location
		was moved to.
		If no sort is needed, both result values will be
		identical.
		"""
		A = self._order
		n = self._count
		A += [0] * (n+1 - len(A))
		m = n+A[n]
		A[n], A[m], self._count = 0, 0, n+1
		return m, n
	
	def remove(self, id: int) -> (int, int):
		"""
		The result of this function is the shuffle performed
		while removing the given item.]
		'
		The first value in the result is the location where
		the removed value was found, and the second value
		is the location where its replacement was found.
		If no shuffle is needed, both result values will be
		identical.
		"""
		A = self._order
		n = self._count - 1
		m = id
		if m >= len(A) or m+A[m] >= self._count:
			raise IndexError()
		A[n], A[m], n, m, self._count = 0, 0, n+A[n], m+A[m], n
		A[n], A[m] = m-n, n-m
		return m, n
	
	def __getitem__(self, id: int) -> int:
		A = self._order
		m = id
		if m >= len(A):
			raise IndexError()
		return m+A[m]
