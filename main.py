# -*- coding:utf-8 -*-
import GUI
import time
import random
import numpy as np
import copy
from functools import total_ordering
from collections import deque


class CellError(Exception): pass


class NoSolution(Exception): pass


class EmptyDomain(Exception): pass


class NotInDomain(Exception): pass


@total_ordering
class Cell:
	def __init__(self, loc, value, grid, given: bool):

		self.loc = loc
		self._value = value
		self.grid = grid
		self._domain = None
		self.given = given

	@property
	def domain(self):
		if self.given:
			raise CellError('This cell is given by the puzzle, it should not have a domain')
		# elif self._value: raise ValueSet('The value of current cell is '+str(self._value))
		else:
			if self._domain is None:
				self.update_domain()
		if not self._domain and not self._value:
			raise EmptyDomain(repr(self))
		return self._domain

	def update_domain(self):
		self._domain = self.grid.get_available_values(self.loc)
		if not self._value:
			# I originally used `and not` instead of two seperate if statement. After thinking about how many times (sometimes a few million) this function is called, I changed it to this way to save some function calls.
			if not self._domain: raise EmptyDomain(repr(self))

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self,
	          n):  # I thought I would never use defensive programming when I am writing a program only by myself :)
		if self.given:
			raise CellError('This cell is given by the puzzle, its value should not be changed')
		else:
			if n:
				try:
					self._domain.remove(n)
				except (KeyError,
				        AttributeError):  # When there is an error try to see if this is caused by the out of date domain
					try:
						self.update_domain()
						self._domain.remove(n)
					except KeyError:
						raise NotInDomain('Value ' + str(n) + ' is not in the domain of ' + repr(self))
					else:
						self._value = n
				else:
					self._value = n
			else:  # when n == 0
				self._domain.add(self._value)
				self._value = 0

	def __int__(self):
		return self._value

	def __repr__(self):
		return '<Cell %d at %s >' % (self._value, str(self.loc))

	def __bool__(self):
		return bool(self._value)

	def __eq__(self, other):
		if isinstance(other, int):
			return self.value == other
		elif isinstance(other, Cell):
			return self.value == other.value
		else:
			raise NotImplementedError('Cannot compare these two types')

	def __lt__(self, other):
		if isinstance(other, int):
			return self.value < other
		elif isinstance(other, Cell):
			return self.value < other.value
		else:
			raise NotImplementedError('Cannot compare these two types')


class Grid:
	def __init__(self, input_string):
		self.cells_to_fill = deque()
		tmp_dict = {}
		for d in range(81):
			tmp_dict[divmod(d, 9)] = int(input_string[d])

		tmp_all = []
		for i in range(9):
			tmp = []
			for j in range(9):
				tmp.append(Cell((j + 1, i + 1), tmp_dict[i, j], self, bool(tmp_dict[i, j])))
				if tmp_dict[i, j] == 0: self.cells_to_fill.append((j + 1, i + 1))

			tmp_all.append(tmp)

		self.map = np.array(tmp_all)
		self.map_t = self.map.transpose()  # use this to access columns(x coordinate)
		self._subgrid = {}

		self.cells_to_fill = deque(sorted(self.cells_to_fill, key=lambda cell: len(
			self[cell].domain)))  # Try to comment out this line for better performance

		del tmp_dict
		del tmp_all
		del tmp

	def goal_check(self):
		if not np.all(self.map):
			return False
		else:
			answer = list(range(1, 10))
			for row in self.map:
				if sorted(row) != answer: return False
			for column in self.map_t:
				if sorted(column) != answer: return False
			for subgrid in self.subgrid.values():
				if sorted(subgrid.map.flatten()) != answer: return False
		return True

	def visualize(self, block=True):
		if block:
			GUI.visualize_board(self.map)
		else:
			self.board = GUI.BoardConnection(self.map)

	def visualize_text(self):
		c = 1
		print('   ', ' '.join([str(t) for t in range(1, 10)]))
		print('   ' + '-' * 19)
		for row in self.map:
			print(c, '|', end=' ')
			c += 1
			for cell in row:
				print(int(cell) if cell else ' ', end=' ')
			print('|')
		print('   ' + '-' * 19)

	def get_neighbours(self, loc):
		x, y = loc
		r = self.map[y - 1].tolist()
		c = self.map_t[x - 1].tolist()
		s = self.subgrid[((y - 1) // 3) * 3 + (x - 1) // 3 + 1].get_neighbours(loc)
		del r[x - 1]
		del c[y - 1]
		return r + c + s

	@property
	def subgrid(self):
		if not self._subgrid: self.initialize_subgrid()
		return self._subgrid

	def initialize_subgrid(self):
		for i in range(1, 10):
			self._subgrid[i] = SubGrid(self, i)

	def copy(self):
		new_grid = Grid.__new__(Grid)
		new_grid.map = copy.deepcopy(self.map)
		new_grid.map_t = new_grid.map.transpose()
		# new_grid.map, new_grid.map_t = self.map.copy(),self.map_t.copy()

		# print(self.cells_to_fill)
		new_grid.cells_to_fill = deque()
		if hasattr(self, 'board'):
			new_grid.board = self.board

		for row in self.map:
			for cell in row:
				if not cell: new_grid.cells_to_fill.append(cell.loc)
		new_grid._subgrid = {}
		return new_grid

	def disconnect_board(self):
		if hasattr(self, 'board'): self.board.disconnect()

	def __getitem__(self, item):
		"""
		:param item: a tuple (x,y)
		:return: 
		"""
		return self.map[item[1] - 1, item[0] - 1]

	def __setitem__(self, key, value):
		if hasattr(self, 'board'):
			self.board.update(key, value)
		self.map[key[1] - 1, key[0] - 1].value = value

	full = set(range(1, 10))

	def get_available_values(self, loc, debug=False):
		"""
		:param loc: a tuple (x,y)
		:return: a set of values available for the cell
	"""
		x, y = loc
		region = ((y - 1) // 3) * 3 + (x - 1) // 3 + 1
		sa = self.subgrid[region].available_values  # sa stand for Sub-grid Available_values
		ra = set()
		ca = set()
		row = self.map[y - 1]
		column = self.map_t[x - 1]

		for cell in row:
			if cell: ra.add(cell._value)
		for cell in column:
			if cell: ca.add(cell._value)

		ra ^= self.full
		ca ^= self.full

		# for n in range(1, 10):
		# 	if n not in row: ra.add(n)
		# 	if n not in column: ca.add(n)

		if debug:
			print(self[loc], 'region No.', region)
			print(sa, ra, ca)
			print('Row:', row)
			print('Column:', column)
			print('Result:', sa & ra & ca)
		return sa & ra & ca


class SubGrid:
	def __init__(self, grid, region):
		"""
		:param grid: A Grid object
		:param region: a int from 1 to 9
		in 9 sub-grid of a grid, region number follow the pattern
		1 2 3
		4 5 6
		7 8 9
		"""
		self.region = region
		y, x = divmod(region - 1, 3)
		y *= 3
		x *= 3
		# print(x,y)
		self._available_values = None
		self.map = np.array([grid.map[y][x:x + 3] for y in range(y, y + 3)])
		self.value = np.sum(self.map.astype(int))

	def __repr__(self):
		return '<Subgrid Object at region ' + str(self.region) + ':\n' + str(self.map) + ' >'

	def __eq__(self, other):
		return np.all(self.map == other.map)

	full = set(range(1, 10))

	def update_available_values(self):
		if self.map.all():
			return set()
		else:
			tmp = self.map.flatten()
			l = set()

			for cell in tmp:
				if cell: l.add(cell._value)

			l ^= self.full

			self._available_values = l
			return l

	def get_neighbours(self, loc):
		x = (loc[0] - 1) // 3
		y = (loc[1] - 1) % 3
		tmp = self.map.tolist()
		del tmp[y][x]

		def flatten(l):
			res = []
			for e in l:
				if isinstance(e, list):
					res += flatten(e)
				else:
					res.append(e)
			return res

		return flatten(tmp)

	@property
	def available_values(self):
		new_value = np.sum(self.map.astype(int))
		if new_value == self.value:
			if self._available_values:
				return self._available_values
		else:
			self.value = new_value
		return self.update_available_values()


def GUItest():
	random_color = lambda: hex(random.randrange(256))[2:].zfill(2)
	b = GUI.BoardConnection('0' * 81)
	start = time.time()
	for i in range(1000):
		b.update((random.randint(1, 9), random.randint(1, 9)), random.randrange(10),
		         '#' + random_color() + random_color() + random_color())
	print(time.time() - start)


def BTS(input_string, display=False):
	def inference():
		def revise(loc):
			cell = grid[loc]
			if len(cell.domain) == 1:
				grid[loc] = cell.domain.copy().pop()
				return True
			return False

		try:
			changed = []
			q = grid.cells_to_fill.copy()
			while len(q):
				loc = q.popleft()
				if revise(loc):
					grid.cells_to_fill.remove(loc)
					changed.append(loc)
					for cell in grid.get_neighbours(loc):
						if not cell:
							q.append(cell.loc)
							cell.update_domain()
		except EmptyDomain:
			for loc in changed[::-1]:
				grid[loc] = 0
				grid.cells_to_fill.append(loc)
				for n in grid.get_neighbours(loc):
					n.update_domain()
			raise
		return changed

	def search(grid):
		if grid.goal_check(): return True

		grid.cells_to_fill = deque(sorted(grid.cells_to_fill, key=lambda cell: len(grid[cell].domain)))

		loc = grid.cells_to_fill.popleft()
		c = grid[loc]
		c.update_domain()

		p = sorted(c.domain)
		for value in p:
			try:
				grid[loc] = value
			except NotInDomain:  # Some outer level inferences caused this
				grid[loc] = 0
				continue

			try:
				for cell in grid.get_neighbours(loc):
					if not cell:
						cell.update_domain()
			except EmptyDomain:  # Arc inconsistency found upon assigning the value, this should be eliminated by inference. But if inference never run for this setting
				grid[loc] = 0
				continue

			try:
				changed = inference()
			except EmptyDomain:  # Arc inconsistency found
				continue

			try:
				search(grid)
			except NoSolution:
				for c in changed[::-1]:  # Reverse "damages"
					grid.cells_to_fill.append(c)
					grid[c] = 0
					for n in grid.get_neighbours(c):
						n.update_domain()
				continue
			except EmptyDomain:
				pass
			else:
				return True

		grid.cells_to_fill.append(loc)
		grid[loc] = 0
		for n in grid.get_neighbours(loc):
			n.update_domain()  # If this raises EmptyDomain then there is some inconsistency that wasn't caught in outer level
		raise NoSolution

	grid = Grid(input_string)

	if display: grid.visualize(False)

	try:
		inference()
		search(grid)
	except (NoSolution,EmptyDomain,IndexError):
		if display: grid.board.pipe.send('NoSolution')
	else:
		solution=''.join(str(c.value) for c in grid.map.flatten())
		if display: grid.board.pipe.send(solution)
		return solution
	finally:
		if display:grid.board.disconnect()



def main(input_string, display=False):
	""":returns: a string represent the solved board"""
	try:
		return BTS(input_string, display)
	except NoSolution:
		return "Invalid Board. No Solution Found."


if __name__ == '__main__':
	main('800000000003600000070090200080007000000045700000100030001000068008500010090000400',True)

