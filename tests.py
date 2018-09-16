from django.test import TestCase
from .models import LEFInstance


class LEFInstanceTestCase(TestCase):

	def test_instance_solvable(self):

		number_of_tries = 100
		print("Generating {} instances".format(number_of_tries))

		fails = 0
		f_instances = list()
		for _ in range(number_of_tries):
			instance = LEFInstance.random(5)
			solutions, metadata = compute_optimal_solutions(instance)
			if len(solutions) > 0:
				print(".", end="", flush=True)
			else:
				print("x", end="", flush=True)
				fails += 1
				f_instances.append(instance)

		print()
		print("Number of fails: {}".format(fails))


def _assertNoEnvyC1(instance, alloc, first_index, second_index, r):
	r_first = instance[first_index].index(r)
	idx_in_prev = instance[first_index].index(alloc[second_index])
	r_scnd = instance[second_index].index(r)
	idx_in_prev2 = instance[second_index].index(alloc[second_index])

	return idx_in_prev > r_first and r_scnd > idx_in_prev2

def _assertNoEnvyC2(instance, alloc, first_index, second_index, r):
	r_first = instance[first_index].index(r)
	idx_in_prev = instance[first_index].index(alloc[first_index])
	r_scnd = instance[second_index].index(r)
	idx_in_prev2 = instance[second_index].index(alloc[first_index])

	return idx_in_prev < r_first and r_scnd < idx_in_prev2


def backtrack_from_agent(instance, agent_idx):
	ca_idx = agent_idx
	alloc = {a: None for a in range(len(instance))}
	impossible_alloc = {a: list() for a in range(len(instance))}
	allocated_resources = list()
	niter = 0
	last_agent_idx = agent_idx-1 if agent_idx != 0 else len(instance)-1
	hotspots = [[0 for _ in range(len(instance))] for _ in range(len(instance))]

	while not alloc[last_agent_idx] != None:

		agent_prefs = instance[ca_idx]
		imp_alloc = impossible_alloc[ca_idx]
		available = [r for r in agent_prefs \
			if r not in allocated_resources and r not in imp_alloc]

		allocation_happened = False
		for r in available:
			niter += 1

			if ca_idx == agent_idx:
				alloc[ca_idx] = r
				allocated_resources.append(r)
				ca_idx = (ca_idx + 1) % len(instance)
				allocation_happened = True
				break

			next_index = (ca_idx + 1) % len(instance)
			if ca_idx == 0:
				if next_index == agent_idx:
					if _assertNoEnvyC2(instance, alloc, next_index, next_index-1, r):
						alloc[ca_idx] = r
						allocated_resources.append(r)
						allocation_happened = True
				else:
					alloc[ca_idx] = r
					allocated_resources.append(r)
					ca_idx = (ca_idx + 1) % len(instance)
					allocation_happened = True
				break

			first_index = ca_idx 
			second_index = ca_idx-1 

			c1 = _assertNoEnvyC1(instance, alloc, first_index, second_index, r)
			c2 = _assertNoEnvyC2(instance, alloc, next_index, next_index-1, r) \
				if next_index == agent_idx and next_index != 0 else True

			if c1 and c2:
				alloc[ca_idx] = r
				allocated_resources.append(r)
				ca_idx = (ca_idx + 1) % len(instance)
				allocation_happened = True
				break

		if not allocation_happened:
			impossible_alloc[ca_idx] = list()
			ca_idx = ca_idx - 1 if ca_idx != 0 else len(instance) - 1
			impossible_alloc[ca_idx].append(alloc[ca_idx])
			allocated_resources.remove(alloc[ca_idx])
			hotspots[instance[ca_idx].index(alloc[ca_idx])][ca_idx] += 1
			alloc[ca_idx] = None

		if ca_idx == agent_idx and len(impossible_alloc[ca_idx]) == len(instance):
			return False, niter, hotspots

	return alloc, niter, hotspots


def compute_optimal_solutions(instance):
	solutions = list()
	metadata = list()
	revrsd_instance = instance[::-1]
	instance_length = len(instance)
	
	for actor_idx in range(instance_length):
		sol, niter, hotspots = backtrack_from_agent(instance, actor_idx)
		if sol and sol not in solutions: 
			# print("solutions: {}".format(solutions))
			# print("Sol: {}".format(sol))
			solutions.append(sol)
			metadata.append({
				'niter': niter,
				'hotspots': hotspots
			})
			
		# compute solution in the reversed order
		sol, niter, hotspots = backtrack_from_agent(revrsd_instance, actor_idx)
		if not sol: continue
		# reverse solution
		reversed_solution = dict()
		l = instance_length - 1
		for a in range(instance_length):
			reversed_solution[a] = sol.get(l - a)

		if reversed_solution not in solutions: 
			solutions.append(reversed_solution)
			metadata.append({
				'niter': niter,
				'hotspots': hotspots
			})

	return solutions, metadata