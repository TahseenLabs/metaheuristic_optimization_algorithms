# Name: Tahseen Ahmad

import unittest
import math
import csv
import random
import copy
import numpy as np
import pyswarms as ps
from simanneal import Annealer
from deap import base, creator, tools

# Creating constants
CXPB = 0.5
MUTPB = 0.2
swarm_best_cost = 1000000
swarm_best_itinerary = []
itineraries = []
home = 11

# UNIT TESTS
class UnitTests (unittest.TestCase):
    # Testing if csv file is read correctly
    def testReadCSV(self):
        rows = readCSVFile('track-locations.csv')
        self.assertEqual('GP', rows[0][0])
        self.assertEqual('Valencia', rows[0][22])
        self.assertEqual('Temp week 52', rows[55][0])
        self.assertEqual('16.25', rows[55][22])
        self.assertEqual('12.5', rows[11][8])
    
    # Testing conversion of string values to float
    def testRowToFloat(self):
        rows = readCSVFile('track-locations.csv')
        convertRowToFloat(rows, 2)
        self.assertAlmostEqual(14.957883, rows[2][1], delta=0.0001)
        self.assertAlmostEqual(39.484786, rows[2][22], delta=0.0001)
        self.assertAlmostEqual(36.532176, rows[2][17], delta=0.0001)
        self.assertAlmostEqual(-38.502284, rows[2][19], delta=0.0001)
        self.assertAlmostEqual(36.709896, rows[2][5], delta=0.0001)
        convertRowToFloat(rows, 5)
        self.assertAlmostEqual(31.5, rows[5][1], delta=0.0001)
        self.assertAlmostEqual(16.5, rows[5][22], delta=0.0001)
        self.assertAlmostEqual(8.5, rows[5][17], delta=0.0001)
        self.assertAlmostEqual(23.5, rows[5][19], delta=0.0001)
        self.assertAlmostEqual(16.5, rows[5][5], delta=0.0001)
    
     # Testing if track locations is read correctly
    def testReadTrackLocations(self):
        rows = readTrackLocations()
        self.assertEqual(rows[0][0], 'Thailand')
        self.assertAlmostEqual(rows[2][0], 14.957883, delta=0.0001)
        self.assertAlmostEqual(rows[55][0], 30.75, delta=0.0001)
        self.assertEqual(rows[0][21], 'Valencia')
        self.assertAlmostEqual(rows[2][21], 39.484786, delta=0.0001)
        self.assertAlmostEqual(rows[4][21], 16, delta=0.0001)
    
    # Testing if race weekends is read correctly
    def testReadRaceWeekends(self):
        weekends = readRaceWeekends()
        self.assertEqual(weekends[0], 8)
        self.assertEqual(weekends[21], 45)
        self.assertEqual(weekends[12], 32)

     # Testing haversine distance calculation
    def testHaversine(self):
        rows = readTrackLocations()
        self.assertAlmostEqual(haversine(rows, 0, 0), 0.0, delta=0.01)
        self.assertAlmostEqual(haversine(rows, 0, 6), 9632.57, delta=0.01)
        self.assertAlmostEqual(haversine(rows, 6, 8), 1283.12, delta=0.01)
        self.assertAlmostEqual(haversine(rows, 8, 12), 445.06, delta=0.01)
    
     # Testing total season distance calculation
    def testDistanceCalculation(self):
        tracks = readTrackLocations()
        weekends = readRaceWeekends()
        self.assertAlmostEqual(calculateSeasonDistance(tracks, weekends, 8), 146768.1778, delta=0.0001)
        self.assertAlmostEqual(calculateSeasonDistance(tracks, weekends, 6), 151481.2754, delta=0.0001)
    
     # Testing temperature constraints
    def testTempConstraint(self):
        tracks = readTrackLocations()
        weekends1 = [8, 10, 12, 14, 16, 18, 20, 22, 24, 25, 27, 28, 32, 33, 35, 36, 38, 39, 41, 42, 44, 45]
        weekends2 = [8, 10, 12, 14, 16, 18, 30, 22, 24, 25, 27, 28, 32, 33, 35, 36, 38, 39, 48, 42, 40, 41]
        self.assertEqual(checkTemperatureConstraint(tracks, weekends1, 20, 35), False)
        self.assertEqual(checkTemperatureConstraint(tracks, weekends2, 20, 35), True)
        
    def testSummerShutdown(self):
        # Testing that no races are scheduled during summer break
        weekends1 = [8, 10, 12, 14, 16, 18, 20, 22, 24, 25, 27, 28, 32, 33, 35, 36, 38, 39, 41, 42, 44, 45]
        weekends2 = [8, 10, 12, 14, 16, 18, 20, 22, 24, 25, 27, 28, 31, 33, 35, 36, 38, 39, 41, 42, 44, 45]
        self.assertEqual(checkSummerShutdown(weekends1), True)
        self.assertEqual(checkSummerShutdown(weekends2), False)

# SIMULATED ANNEALING CLASS
class CalendarAnnealer(Annealer):
    # This class optimizes calendar using simulated annealing
    def __init__(self, weekends, home, tracks):
        self.state = copy.copy(weekends)
        self.home = home # Home base
        self.tracks = tracks
        super(CalendarAnnealer, self).__init__(self.state)

    def move(self):
        coldest = indexLowestTemp(self.tracks, self.state, 15)
        if coldest != -1 and coldest != 21:
            swapIndex(self.state, coldest)
            return
        hottest = indexHighestTemp(self.tracks, self.state, 35)
        if hottest != -1 and hottest != 21:
            swapIndex(self.state, hottest)
            return
        num_swaps = 1
        if random.random() < 0.1:
            num_swaps = random.randint(2, 3)
        for _ in range(num_swaps):
            swapPair(self.state)
        
    def energy(self):
        return calculateSeasonDistancePenalties(self.tracks, self.state, self.home, 15, 35)

# GENETIC ALGORITHM CLASS
class CalendarGA:
    # Wrapper class for genetic algorithm
    def __init__(self, weekends):
        self.weekends = weekends
        
# Distance calculations
def calculateSeasonDistance(tracks, weekends, home):
    # Calculating total travel distance for season
    total_distance = 0.0
    
    # Sorting races by week number
    indexed_weekends = [(track_idx, weekends[track_idx]) for track_idx in range(len(weekends))]
    sorted_by_week = sorted(indexed_weekends, key=lambda x: x[1])
    
    # Distance from home to 1st race
    first_track = sorted_by_week[0][0]
    total_distance += haversine(tracks, home, first_track)
    
    # Distance between races
    for i in range(len(sorted_by_week) - 1):
        current_track, current_week = sorted_by_week[i]
        next_track, next_week = sorted_by_week[i + 1]
        
        if next_week - current_week == 1:
            total_distance += haversine(tracks, current_track, next_track)
        else:
            total_distance += haversine(tracks, current_track, home)
            total_distance += haversine(tracks, home, next_track)
    
    # Distance from last race back to home
    last_track = sorted_by_week[-1][0]
    total_distance += haversine(tracks, last_track, home)
    return total_distance

def calculateSeasonDistancePenalties(tracks, weekends, home, min, max):
    # Adding penalties if constraints are broken
    distance = calculateSeasonDistance(tracks, weekends, home)
    if not checkTemperatureConstraint(tracks, weekends, min, max):
        distance += 100000
    if not checkSummerShutdown(weekends):
        distance += 100000
    return distance

# CONSTRAINT CHECKS
def checkTemperatureConstraint(tracks, weekends, min, max):
    # Checking if all races are within temp limits
    for race_index in range(len(weekends)):
        week_number = weekends[race_index]
        temp_row = 3 + week_number
        temp = tracks[temp_row][race_index]
        if temp < min or temp > max:
            return False
    return True

def checkSummerShutdown(weekends):
    # Ensuring no race is scheduled in summer shutdown weeks
    shutdown_weeks = [29, 30, 31]
    for week in weekends:
        if week in shutdown_weeks:
            return False
    return True

# Genetic algorithm helper functions
def childGeneticCodeFix(child):
    original = readRaceWeekends()   # Original correct list of race weeks
    seen = set()                    # Storing unique weeks already used
    duplicates = []                 # Storing indexes where duplicates appear
    
    # Finding duplicate weeks
    for i, week in enumerate(child.weekends):
        if week in seen:
            duplicates.append(i)  # Saving index of duplicate
        else:
            seen.add(week)
    
    # Finding missing weeks that are not used
    missing = [week for week in original if week not in seen]
    random.shuffle(missing)    # Shuffling missing weeks randomly
    
    # Replacing duplicate weeks with missing weeks
    for i, dup_idx in enumerate(duplicates):
        if i < len(missing):
            child.weekends[dup_idx] = missing[i]

def convertRowToFloat(rows, row_index):
    # Converting all string values in a row to float except for the 1st one
    for col in range(1, len(rows[row_index])):
        rows[row_index][col] = float(rows[row_index][col])

# Counting how many elements are greater than or equal to given value
def countGreaterEqual(array, value):
    count = 0
    for element in array:
        if element >= value:
            count += 1
    return count

# Performing crossover between two GA individuals
def crossoverStrategy(ind1, ind2):
    child1_weekends = []
    child2_weekends = []
    for i in range(len(ind1.weekends)):
        # Keeping last race fixed 
        if i == 21:
            child1_weekends.append(ind1.weekends[i])
            child2_weekends.append(ind2.weekends[i])
        # Randomly picking week from parents
        else:
            child1_weekends.append(rouletteWheel(ind1.weekends[i], ind2.weekends[i]))
            child2_weekends.append(rouletteWheel(ind2.weekends[i], ind1.weekends[i]))
    
    # Updating individuals
    ind1.weekends = child1_weekends
    ind2.weekends = child2_weekends
    
    # Fixing duplicates & missing weeks
    childGeneticCodeFix(ind1)
    childGeneticCodeFix(ind2)
    return ind1, ind2

def evaluateStrategy(individual):
    # Function for GA 
    tracks = readTrackLocations()
    home = 8
    distance = calculateSeasonDistancePenalties(tracks, individual.weekends, home, 15, 35)
    return (distance,)

def generateInitialItineraries(num_particles, initial_solution):
    # Creating initial solutions for PSO
    global itineraries
    itineraries = []
    for _ in range(num_particles):
        shuffled = generateShuffledItinerary(initial_solution)
        itineraries.append(shuffled)
    return itineraries

def generateShuffledItinerary(weekends):
    # Randomly shuffling race weeks except the last one
    shuffled = copy.copy(weekends)
    to_shuffle = shuffled[:-1]  # Keeping last race fixed
    random.shuffle(to_shuffle)
    
    for i in range(len(to_shuffle)):
        shuffled[i] = to_shuffle[i]
    return shuffled

# Haversine distance function
def haversine(rows, location1, location2):
    R = 6371.0
    lat1 = math.radians(rows[2][location1])
    lon1 = math.radians(rows[3][location1])
    lat2 = math.radians(rows[2][location2])
    lon2 = math.radians(rows[3][location2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Creating a new GA individual
def initIndividual(ind_class):
    weekends = readRaceWeekends()
    shuffled = generateShuffledItinerary(weekends)
    return ind_class(shuffled)

def indexHighestTemp(tracks, weekends, max):
    # Finding race with temp above maximum
    highest_temp = max
    highest_index = -1
    
    for race_index in range(len(weekends)):
        week_number = weekends[race_index]
        temp_row = 3 + week_number
        temp = tracks[temp_row][race_index]
        
        if temp > highest_temp:
            highest_temp = temp
            highest_index = race_index
    return highest_index

def indexLowestTemp(tracks, weekends, min):
    # Finding race with temp below minimum
    lowest_temp = min
    lowest_index = -1
    
    for race_index in range(len(weekends)):
        week_number = weekends[race_index]
        temp_row = 3 + week_number
        temp = tracks[temp_row][race_index]
        
        if temp < lowest_temp:
            lowest_temp = temp
            lowest_index = race_index
    return lowest_index

def mutateIndividual(individual, indpb):
    # Mutation function for GA
    tracks = readTrackLocations()
    
    # Fixing cold races first
    coldest = indexLowestTemp(tracks, individual.weekends, 15)
    if coldest != -1 and coldest != 21:
        swapIndex(individual.weekends, coldest)
        return (individual,)
    
    # Fixing hot races
    hottest = indexHighestTemp(tracks, individual.weekends, 35)
    if hottest != -1 and hottest != 21:
        swapIndex(individual.weekends, hottest)
        return (individual,)
    # Otherwise we random swap
    swapPair(individual.weekends)
    return (individual,)

def objectiveCalendar(particles):
    # Cost function used by PSO
    global itineraries, swarm_best_cost, swarm_best_itinerary
    
    tracks = readTrackLocations()
    home_base = 8
    costs = []
    
    for i, particle in enumerate(particles):
        itinerary = copy.copy(itineraries[i])
        
        # Applying particle changes
        swapElements(itinerary, particle)
        # Fixing temperature violations
        coldest = indexLowestTemp(tracks, itinerary, 15)
        while coldest != -1 and coldest != 21:
            swapIndex(itinerary, coldest)
            coldest = indexLowestTemp(tracks, itinerary, 15)
            
        hottest = indexHighestTemp(tracks, itinerary, 35)
        while hottest != -1 and hottest != 21:
            swapIndex(itinerary, hottest)
            hottest = indexHighestTemp(tracks, itinerary, 35)
        # Calculating cost
        cost = calculateSeasonDistancePenalties(tracks, itinerary, home_base, 15, 35)
        costs.append(cost)
        
         # Updating global best
        if cost < swarm_best_cost:
            swarm_best_cost = cost
            swarm_best_itinerary = copy.copy(itinerary)
        itineraries[i] = itinerary
    return np.array(costs)

# Printing race calendar
def printItinerary(tracks, weekends, home):
    print("\n" + "=" * 60)
    print("RACE CALENDAR ITINERARY")
    print("=" * 60)
    print(f"Home Base: {tracks[0][home]}")
    print("-" * 60)
    for i, week in enumerate(weekends):
        track_name = tracks[0][i]
        temp_row = 3 + week
        temp = tracks[temp_row][i]
        print(f"Race {i+1:2}: Week {week:2} - {track_name:15} (Temp: {temp:.1f}°C)")
    print("-" * 60)
    total_distance = calculateSeasonDistance(tracks, weekends, home)
    print(f"Total Season Distance: {total_distance:,.2f} km")
    temp_ok = checkTemperatureConstraint(tracks, weekends, 15, 35)
    summer_ok = checkSummerShutdown(weekends)
    print(f"Temperature Constraint (15-35°C): {'PASS' if temp_ok else 'FAIL'}")
    print(f"Summer Shutdown (weeks 29-31): {'PASS' if summer_ok else 'FAIL'}")
    print("=" * 60 + "\n")

# File reading functions
def readCSVFile(file):
    rows = []     # List to store rows
    csv_file = open(file) # Opening file
    csv_reader = csv.reader(csv_file, delimiter=',')
    
    # Reading each row and then storing it
    for row in csv_reader:
        rows.append(row)
    csv_file.close()  # Closing file after reading
    return rows

def readRaceWeekends():
    # Reading race weekend numbers from file
    rows = readCSVFile('race-weekends.csv')
    weekends = []
    
    # Skipping header row & read weekend no.s
    for i in range(1, len(rows)):
        weekends.append(int(rows[i][1]))
    return weekends

# Reading track names, locations & temp data
def readTrackLocations():
    rows = readCSVFile('track-locations.csv')
    # Converting numeric rows to float 
    for row_index in range(2, len(rows)):
        convertRowToFloat(rows, row_index)
    # Removing 1st column
    for row in rows:
        row.pop(0)
    return rows

# Random selection helper
def rouletteWheel(a, b):
    # Randomly selecting one of two values 50/50 chance
    if random.random() < 0.5:
        return a
    else:
        return b

# Swap & mutation helper
def swapElements(itinerary, particle):
    # Swapping multiple race weeks based on PSO values
    indexes = swapIndexes(particle)
    indexes = [i for i in indexes if i < 21]
    # No swaps needed
    if len(indexes) == 0:
        return
    # Swapping one index only
    elif len(indexes) == 1:
        swapIndex(itinerary, indexes[0])
    # Swapping multiple indexes
    else:
        values = [itinerary[i] for i in indexes]
        random.shuffle(values)
        
        for i, idx in enumerate(indexes):
            itinerary[idx] = values[i]

def swapIndexes(particle):
     # Finding indexes where particle value is high 
    indexes = []
    for i in range(len(particle)):
        if particle[i] >= 0.5:
            indexes.append(i)
    return indexes

def swapPair(itinerary):
    # Randomly swapping 2 different races
    idx1 = random.randint(0, 20)
    idx2 = random.randint(0, 20)
    # Ensuring indexes are different
    while idx2 == idx1:
        idx2 = random.randint(0, 20)
    itinerary[idx1], itinerary[idx2] = itinerary[idx2], itinerary[idx1]

def swapIndex(itinerary, index):
    # Swapping one specific race with another random one 
    other = random.randint(0, 20)
    # Ensuring different index
    while other == index:
        other = random.randint(0, 20)
    itinerary[index], itinerary[other] = itinerary[other], itinerary[index]

# Simulated Annealing
def SAcases():
    # Running SA optimization
    tracks = readTrackLocations()
    weekends = readRaceWeekends()
    home = 8
    print("\n" + "=" * 60)
    print("SIMULATED ANNEALING - MotoGP Calendar Optimization")
    print("=" * 60)
    print(f"\nOriginal Distance: {calculateSeasonDistance(tracks, weekends, home):,.2f} km")
    initial_weekends = generateShuffledItinerary(weekends)
    annealer = CalendarAnnealer(initial_weekends, home, tracks)
    annealer.steps = 100000  # Number of SA iterations
    # I disabled default SA progress updates to make overall output cleaner
    annealer.updates = 0 
    
    print("Running Simulated Annealing with 100,000 steps...")
    
    best_state, best_energy = annealer.anneal()
    
    print("\n" + "-" * 60)
    print(f"BEST SOLUTION FOUND: {best_energy:,.2f} km")
    print("-" * 60)
    
    printItinerary(tracks, best_state, home)
    return best_state, best_energy

# Genetic Algorithm
def GAcases():
    # Running GA optimization
    tracks = readTrackLocations()
    weekends = readRaceWeekends()
    home = 8
    
    print("\n" + "=" * 60)
    print("GENETIC ALGORITHM - MotoGP Calendar Optimization")
    print("=" * 60)
    print(f"\nOriginal Distance: {calculateSeasonDistance(tracks, weekends, home):,.2f} km")
    print("Population: 300, Generations: 1000")
    
    if not hasattr(creator, "FitnessMin"):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", CalendarGA, fitness=creator.FitnessMin)
        
    toolbox = base.Toolbox()
    # Registering GA operations
    toolbox.register("individual", initIndividual, creator.Individual)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", evaluateStrategy)
    toolbox.register("mate", crossoverStrategy)
    toolbox.register("mutate", mutateIndividual, indpb=MUTPB)
    toolbox.register("select", tools.selTournament, tournsize=3)
    
    print("Creating initial population...")
    
    population = toolbox.population(n=300)
    fitnesses = list(map(toolbox.evaluate, population))
    for ind, fit in zip(population, fitnesses):
        ind.fitness.values = fit
        
    print("Running 1000 generations...")
    
    for gen in range(1000):
        offspring = toolbox.select(population, len(population))
        offspring = list(map(copy.deepcopy, offspring))
        
        # Crossover
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
                
        # Mutation
        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        # Re-evaluating invalid individuals
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            
        population[:] = offspring
        
    # Findind best solution
    fits = [ind.fitness.values[0] for ind in population]
    best_idx = fits.index(min(fits))
    best_individual = population[best_idx]
    
    print("\n" + "-" * 60)
    print(f"BEST SOLUTION FOUND: {min(fits):,.2f} km")
    print("-" * 60)
    printItinerary(tracks, best_individual.weekends, home)
    return best_individual.weekends, min(fits)

# Particle Swarm Optimisation
def PSOcases():
    # Running PSO
    global swarm_best_cost, swarm_best_itinerary, itineraries
    tracks = readTrackLocations()
    weekends = readRaceWeekends()
    home = 8
    
    print("\n" + "=" * 60)
    print("PARTICLE SWARM OPTIMIZATION - MotoGP Calendar")
    print("=" * 60)
    print(f"\nOriginal Distance: {calculateSeasonDistance(tracks, weekends, home):,.2f} km")
    print("Particles: 100, Iterations: 1000")
    
    swarm_best_cost = 1000000
    swarm_best_itinerary = []
    
    generateInitialItineraries(100, weekends)
    
    options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
    bounds = (np.zeros(22), np.ones(22))
    optimizer = ps.single.GlobalBestPSO(n_particles=100, dimensions=22, options=options, bounds=bounds)
    
    print("Running PSO optimization...")
    # I made verbose value false to make overall output cleaner
    best_cost, best_pos = optimizer.optimize(objectiveCalendar, iters=1000, verbose=False) 
    
    print("\n" + "-" * 60)
    print(f"BEST SOLUTION FOUND: {swarm_best_cost:,.2f} km")
    print("-" * 60)
    
    printItinerary(tracks, swarm_best_itinerary, home)
    return swarm_best_itinerary, swarm_best_cost

if __name__ == '__main__':
    # unittest.main() # For unit tests
    SAcases()   # Simulated Annealing
    GAcases()   # Genetic Algorithm
    PSOcases()  # Particle Swarm Optimization





