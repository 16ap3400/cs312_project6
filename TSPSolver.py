#!/usr/bin/python3

from which_pyqt import PYQT_VER
if PYQT_VER == 'PYQT5':
	from PyQt5.QtCore import QLineF, QPointF
elif PYQT_VER == 'PYQT4':
	from PyQt4.QtCore import QLineF, QPointF
else:
	raise Exception('Unsupported Version of PyQt: {}'.format(PYQT_VER))




import time
import numpy as np
from TSPClasses import *
import heapq
import itertools
import sys



class TSPSolver:
	def __init__( self, gui_view ):
		self._scenario = None

	def setupWithScenario( self, scenario ):
		self._scenario = scenario


	''' <summary>
		This is the entry point for the default solver
		which just finds a valid random tour.  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of solution, 
		time spent to find solution, number of permutations tried during search, the 
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''
	
	def defaultRandomTour( self, time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		foundTour = False
		count = 0
		bssf = None
		start_time = time.time()
		while not foundTour and time.time()-start_time < time_allowance:
			# create a random permutation
			perm = np.random.permutation( ncities )
			route = []
			# Now build the route using the random permutation
			for i in range( ncities ):
				route.append( cities[ perm[i] ] )
			bssf = TSPSolution(route)
			count += 1
			if bssf.cost < np.inf:
				# Found a valid route
				foundTour = True
		end_time = time.time()
		results['cost'] = bssf.cost if foundTour else math.inf
		results['time'] = end_time - start_time
		results['count'] = count
		results['soln'] = bssf
		results['max'] = None
		results['total'] = None
		results['pruned'] = None
		return results


	''' <summary>
		This is the entry point for the greedy solver, which you must implement for 
		the group project (but it is probably a good idea to just do it for the branch-and
		bound project as a way to get your feet wet).  Note this could be used to find your
		initial BSSF.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found, the best
		solution found, and three null values for fields not used for this 
		algorithm</returns> 
	'''

	def greedy( self,time_allowance=60.0 ):
		results = {}
		cities = self._scenario.getCities()
		ncities = len(cities)
		count = 0

		route = []
		found_route = True
		start_time = time.time()
		starting_city = None
		name_route = []
		for i in range(len(cities)):

			curr_city = cities[i]
			starting_city = cities[i]
			route = []
			name_route = []
			route.append(curr_city)
			name_route.append(curr_city._name)
			found_route = True
			count += 1

			while True:
				min_route_cost = np.inf
				lowest_cost_city = None
				for city in cities:
					city_cost = curr_city.costTo(city)
					if city not in route and city_cost < min_route_cost:
						min_route_cost = city_cost
						lowest_cost_city = city

				if lowest_cost_city is not None:
					curr_city = lowest_cost_city
					route.append(curr_city)
					name_route.append(curr_city._name)
				else:
					# Check to if any city has been missed.
					for city in cities:
						if city not in route:
							found_route = False
							break
					# Leave infinite loop
					break

			# If all cities in route, break and return result, else, continue
			to_start_cost = route[-1].costTo(starting_city)
			if found_route and to_start_cost != np.inf:
				break

		if found_route:
			bssf = TSPSolution(route)
			end_time = time.time()
			results['cost'] = bssf.cost
			results['time'] = end_time - start_time
			results['count'] = count
			results['soln'] = bssf
			results['max'] = None
			results['total'] = None
			results['pruned'] = None
		else:
			# No route was found.
			end_time = time.time()
			results['cost'] = math.inf
			results['time'] = end_time - start_time
			results['count'] = count
			results['soln'] = math.inf
			results['max'] = None
			results['total'] = None
			results['pruned'] = None

		return results












	
	
	
	''' <summary>
		This is the entry point for the branch-and-bound algorithm that you will implement
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number solutions found during search (does
		not include the initial BSSF), the best solution found, and three more ints: 
		max queue size, total number of states created, and number of pruned states.</returns> 
	'''
		
	def branchAndBound( self, time_allowance=60.0 ):
		results = {}
		count = 0
		max_queue_size = 0
		total_states_created = 0
		total_states_pruned = 0
		initial_rough_bound = 0.0
		self.BSSF = np.inf
		cities = self._scenario.getCities()
		ncities = len(cities)
		priority_queue = []
		heapq.heapify(priority_queue)
		# --- Space Complexity: O(n^2) -- Initializes a 2d array by the number of cities.
		row_reduced_matrix = [[np.inf] * ncities for i in range(ncities)]

		# Initialize matrix
		# --- Time Complexity: O(n^2) -- In order to initialize the 2d array of the same cities.
		for i in range(ncities):
			for j in range(ncities):
				row_reduced_matrix[i][j] = cities[i].costTo(cities[j])

		row_reduced_matrix, initial_rough_bound = self.reduce_matrix(row_reduced_matrix, ncities)

		# If everything is unreachable, it's probably good to know at the beginning.
		if initial_rough_bound == 0.0:
			raise Exception("Initial Rough Bound cannot be 0 (unless everything is unreachable)")

		# Get initial BSSF from greedy algorithm
		greedy_result = TSPSolver.greedy(self)
		self.BSSF = greedy_result['cost']

		# Initialize the result to the greedy result.
		results = greedy_result

		# Push on the initial state for all cities.
		# --- Time Complexity: O(n) -- In order to iterate through all the cities.
		for city in cities:
			initial_state = State(initial_rough_bound, [city], row_reduced_matrix, 0)
			heapq.heappush(priority_queue, initial_state)


		start_time = time.time()
		# While states are in the queue and it is within the allotted amount of time. Do the TSP.
		# --- Time Complexity: O(n!) -- Goes through each branch in order to find the optimal route.
		while len(priority_queue) != 0 and time.time() - start_time < time_allowance:

			# Update the max queue size
			if len(priority_queue) > max_queue_size:
				max_queue_size = len(priority_queue)

			# Pop off the next highest priority state (based on state's bssf compared to the initial/updated BSSF).
			curr_state = heapq.heappop(priority_queue)

			if curr_state._bound < self.BSSF:
				# Check all next connections from the current state (that that haven't already been attempted)
				# --- Time Complexity: O(n) -- Goes through all the cities that are not currently in the current state's route.
				for to_city in cities:
					if to_city not in curr_state._route:
						# Updated curr_matrix to the curr_state's matrix.
						# --- Time Complexity: O(n^2) -- Creates a new matrix and copies all values from parent matrix over.
						# --- Space Complexity: O(n^2) -- Allocates space for new 2d array.
						new_matrix = [[np.inf] * ncities for i in range(ncities)]
						new_bound = curr_state._bound
						for i in range(ncities):
							for j in range(ncities):
								new_matrix[i][j] = curr_state._reduced_matrix[i][j]

						# Update bound with cost from -> to city.
						from_city = curr_state._route[-1]
						cost_from_last_city_to_curr_city = new_matrix[from_city._index][to_city._index]
						new_bound += cost_from_last_city_to_curr_city

						# Make row of from_city inf and make col of to_city inf (plus the inverse of the from_city,to_city).
						# ---- Time Complexity: O(n^2) --- Goes through and updates no longer valid areas to infinity.
						for i in range(ncities):
							for j in range(ncities):
								if i == from_city._index or j == to_city._index or (i == to_city._index and j == from_city._index):
									new_matrix[i][j] = np.inf

						# Row reduces the current matrix. ---------------------- O(n^2+n^2) --- Goes through the matrix twice, to row and column reduce.
						new_matrix, updated_bound = self.reduce_matrix(new_matrix, ncities)

						# Update bound with new row reduced matrix (add to bound any rows or columns that needed to be updated).
						new_bound += updated_bound
						new_route = curr_state._route.copy()
						new_route.append(to_city)

						# Create new state and increase the depth from its parent state.
						new_state = State(new_bound, new_route, new_matrix, curr_state._depth+1)

						# If no more cities to add, updated BSSF if able to connect back to start.
						if new_state._depth == (ncities - 1):
							bssf = TSPSolution(new_state._route)
							if bssf.cost != np.inf and bssf.cost < self.BSSF:
								results.clear()
								end_time = time.time()
								count += 1
								self.BSSF = bssf.cost
								results['cost'] = bssf.cost
								results['time'] = end_time - start_time
								results['count'] = count
								results['soln'] = bssf
								results['max'] = max_queue_size
								results['total'] = total_states_created
								results['pruned'] = total_states_pruned
						elif new_bound < self.BSSF:
							# If the new state's bound is better than the current BSSF, then add to the priority queue.
							total_states_created += 1
							heapq.heappush(priority_queue, new_state)
						else:
							# This state has been initially pruned.
							total_states_pruned += 1
			else:
				# If bound is greater than the current BSSF, then calculate all the branches that
				# were pruned by not going down this branch (factorial of number of levels left).
				# num_levels_left = ((ncities - 1) - curr_state._depth)
				# total_states_pruned += math.factorial(num_levels_left)
				total_states_pruned += 1
		# Return the best results (either optimal or best within the time limit.
		return results







	''' <summary>
		This is the entry point for the algorithm you'll write for your group project.
		</summary>
		<returns>results dictionary for GUI that contains three ints: cost of best solution, 
		time spent to find best solution, total number of solutions found during search, the 
		best solution found.  You may use the other three field however you like.
		algorithm</returns> 
	'''
		
	def fancy( self,time_allowance=60.0 ):
		# try:
		# 	filename = sys.argv[1]
		# 	root = sys.argv[2]
		# except IndexError:
		# 	sys.stderr.write('no input and/or root node specified\n')
		# 	sys.stderr.write('usage: python edmonds.py <file> <root>\n')
		# 	sys.exit(1)

		# prices,names = self._input(filename)

		cities = self._scenario.getCities()
		ncities = len(cities)

		arcs = []
		for city in cities:
			for inner_city in cities:
				if inner_city != city:
					arcs.append((city,inner_city))


		g = self._load(arcs)
		h = self.mst(int(cities[0]._index),g)
		for s in h:
			for t in h[s]:
				print("%d-%d" % (s,t))



	# --------------------------------------------------------------------------------- #

	def _input(self, filename):
		prices = {}
		names = {}

		for line in open(filename, "r").readlines():
			(name, src, dst, price) = line.rstrip().split()
			name = int(name.replace('M',''))
			src = int(src.replace('C',''))
			dst = int(dst.replace('C',''))
			price = int(price)
			t = (src,dst)
			if t in prices and prices[t] <= price:
				continue
			prices[t] = price
			names[t] = name

		return prices,names

	def _load(self, arcs):
		g = {}
		for (src,dst) in arcs:
			if src in g:
				g[src._index][dst._index] = src.costTo(dst)
			else:
				g[src._index] = { dst : src.costTo(dst) }
		return g

	def _reverse(self, graph):
		r = {}
		for src in graph:
			for (dst,c) in graph[src._index]:
				if dst in r:
					r[dst._index][src._index] = c
				else:
					r[dst._index] = { src : c }
		return r

	def _getCycle(self, n, g, visited=None, cycle=None):
		if visited is None:
			visited = set()
		if cycle is None:
			cycle = []
		visited.add(n)
		cycle += [n]
		if n not in g:
			return cycle
		for e in g[n]:
			if e not in visited:
				cycle = self._getCycle(e,g,visited,cycle)
		return cycle

	def _mergeCycles(self, cycle,G,RG,g,rg):
		allInEdges = []
		minInternal = None
		minInternalWeight = sys.maxint

		# find minimal internal edge weight
		for n in cycle:
			for e in RG[n]:
				if e in cycle:
					if minInternal is None or RG[n][e] < minInternalWeight:
						minInternal = (n,e)
						minInternalWeight = RG[n][e]
						continue
				else:
					allInEdges.append((n,e))

					# find the incoming edge with minimum modified cost
		minExternal = None
		minModifiedWeight = 0
		for s,t in allInEdges:
			u,v = rg[s].popitem()
			rg[s][u] = v
			w = RG[s][t] - (v - minInternalWeight)
			if minExternal is None or minModifiedWeight > w:
				minExternal = (s,t)
				minModifiedWeight = w

		u,w = rg[minExternal[0]].popitem()
		rem = (minExternal[0],u)
		rg[minExternal[0]].clear()
		if minExternal[1] in rg:
			rg[minExternal[1]][minExternal[0]] = w
		else:
			rg[minExternal[1]] = { minExternal[0] : w }
		if rem[1] in g:
			if rem[0] in g[rem[1]]:
				del g[rem[1]][rem[0]]
		if minExternal[1] in g:
			g[minExternal[1]][minExternal[0]] = w
		else:
			g[minExternal[1]] = { minExternal[0] : w }

	# --------------------------------------------------------------------------------- #

	def mst(self, root,G):
		""" The Chu-Lui/Edmond's algorithm
		arguments:
		root - the root of the MST
		G - the graph in which the MST lies
		returns: a graph representation of the MST
		Graph representation is the same as the one found at:
		http://code.activestate.com/recipes/119466/
		Explanation is copied verbatim here:
		The input graph G is assumed to have the following
		representation: A vertex can be any object that can
		be used as an index into a dictionary.  G is a
		dictionary, indexed by vertices.  For any vertex v,
		G[v] is itself a dictionary, indexed by the neighbors
		of v.  For any edge v->w, G[v][w] is the length of
		the edge.  This is related to the representation in
		<http://www.python.org/doc/essays/graphs.html>
		where Guido van Rossum suggests representing graphs
		as dictionaries mapping vertices to lists of neighbors,
		however dictionaries of edges have many advantages
		over lists: they can store extra information (here,
		the lengths), they support fast existence tests,
		and they allow easy modification of the graph by edge
		insertion and removal.  Such modifications are not
		needed here but are important in other graph algorithms.
		Since dictionaries obey iterator protocol, a graph
		represented as described here could be handed without
		modification to an algorithm using Guido's representation.
		Of course, G and G[v] need not be Python dict objects;
		they can be any other object that obeys dict protocol,
		for instance a wrapper in which vertices are URLs
		and a call to G[v] loads the web page and finds its links.
		"""

		RG = self._reverse(G)
		if root in RG:
			RG[root] = {}
		g = {}
		for n in RG:
			if len(RG[n]) == 0:
				continue
			minimum = float("inf")
			s,d = None,None
			for e in RG[n]:
				if RG[n][e] < minimum:
					minimum = RG[n][e]
					s,d = n,e
			if d in g:
				g[d][s] = RG[s][d]
			else:
				g[d] = { s : RG[s][d] }

		cycles = []
		visited = set()
		for n in g:
			if n not in visited:
				cycle = self._getCycle(n,g,visited)
				cycles.append(cycle)

		rg = self._reverse(g)
		for cycle in cycles:
			if root in cycle:
				continue
			self._mergeCycles(cycle, G, RG, g, rg)

		return g

	# --------------------------------------------------------------------------------- #























	def reduce_matrix(self, row_reduced_matrix, ncities):
		# Reduce rows.
		updated_bound = 0.0
		for i in range(ncities):
			min_row_value = np.inf
			for j in range(ncities):
				if row_reduced_matrix[i][j] < min_row_value:
					min_row_value = row_reduced_matrix[i][j]
			for j in range(ncities):
				if min_row_value != np.inf:
					row_reduced_matrix[i][j] -= min_row_value
			if min_row_value != np.inf:
				updated_bound += min_row_value

		# Reduce columns.
		for i in range(ncities):
			min_col_value = np.inf
			for j in range(ncities):
				if row_reduced_matrix[j][i] < min_col_value:
					min_col_value = row_reduced_matrix[j][i]
			for j in range(ncities):
				if min_col_value != np.inf:
					row_reduced_matrix[j][i] -= min_col_value
			if min_col_value != np.inf:
				updated_bound += min_col_value

		return row_reduced_matrix, updated_bound


class State:
	def __init__( self, bound, route, reduced_matrix, depth ):
		self._bound = bound
		self._route = route
		self._reduced_matrix = reduced_matrix
		self._depth = depth

	def __lt__(self, other):
		if self._depth > other._depth:
			return True
		elif self._bound < other._bound:
			return True
		else:
			return False
		



