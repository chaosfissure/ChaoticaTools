import sys
import os

def isCorrect(filename,directory):
	return input('Is ' + filename + ' in ' + directory + ' the correct file? (y/n) =>').lower() == "y"

def ignoreCaseCount(searchInThisString,searchForTerm):
	return searchForTerm.lower() in searchInThisString.lower()


def dirSearch(searchterm, modificationFunc):

	ls = os.listdir(os.getcwd())
	folders = [x for x in ls if os.path.isdir(x)]
	files   = [x for x in ls if x.endswith('.chaos') and not os.path.isdir(x)]
		
	folders.sort(key=os.path.getmtime, reverse=True)
		
	for f in files:
		if ignoreCaseCount(f,searchterm) and isCorrect(f, os.getcwd()):
			modificationFunc(os.path.join(os.getcwd(), f))
			return True
			
							
	cwd = os.getcwd()
	for folder in folders:
		print("Searching in", folder)
		os.chdir(os.path.join(cwd,folder))
		result = dirSearch(searchterm, modificationFunc)
		os.chdir(cwd)
		if result: return True
			
	return False

def isWeight(line):
	if line is None: return False
	if line.count('\t') != 6: return False
	if 'weight"' not in line: return False
	if 'real name="i' not in line.lower(): return False
	
	return True

def modificationFunc(filename):
	
	lines = []
	rewritten = filename.replace('.chaos', '_rewritten.chaos')
	
	if os.path.exists(rewritten):
		with open(rewritten, 'r') as f: lines = f.readlines()
			
	if len(lines) == 0:
		with open(filename, 'r') as f: lines = f.readlines()
	
	contents = []
	weightvals = []
	
	iterOn = -1
	onIterWeights = False
	
	for line in lines:
		if onIterWeights:
			if '</node>' in line:
				onIterWeights = False
				continue
			else:
				name = line[line.index('<real name="') + len('<real name="') : line.index(' weight">')]
				contents[-1].append(name)
				
				weightval = line[line.index('weight">') + len('weight">') : line.index('</real>')]
				weightvals[-1].append(weightval)
		
		elif '<iterator name=' in line:
			iterOn += 1
			name = line[line.index('name="') + len('name="'):line.index('">')].strip()
			contents.append([name])
			weightvals.append([])
		elif '<node name="per_iterator_weights">' in line:
			onIterWeights = True
								
		
	remake = False
	for i, elem in enumerate(contents):
		
		# Check the name of the iterator
		checkNameWith = 'Iterator ' + str(i+1)
		if elem[0] != checkNameWith:
			print('Iterator', i, 'name not consistent.  Remaking!')
			print('\t', checkNameWith, elem[0])
			remake = True
			break
		for j, eachIter in enumerate(elem[1:]):
			requireIter = 'Iterator ' + str(j+1)
			if requireIter != eachIter:
				print('Weight on iter', i, 'not consistent. Remaking!')
				print('\t', requireIter, eachIter)
				remake = True
				break
				
	if remake:
		print('Remaking chaos file with consistent iter/weight combinations for editing.')
		with open(rewritten, 'w') as f:
			
			iterOn = 0
			numWeights = len(contents)
			
			lines = [None if 'per_iterator_weights' in x else x for x in lines]
			lines = [x for x in lines if not isWeight(x)]
			
			for line in lines:
				if line is None:
					f.write('\t\t\t\t\t<node name="per_iterator_weights">\n')
					for i, weight in enumerate(weightvals[iterOn-1]):
						lineval = '\t\t\t\t\t\t'
						lineval += '<real name="Iterator '
						lineval += str(i+1)
						lineval += ' weight">'
						lineval += weight
						lineval += '</real>\n'
						f.write(lineval)
				elif '<iterator name=' in line:
					iterOn += 1
					f.write('\t\t\t<iterator name="Iterator ' + str(iterOn) + '">\n')
				else:
					f.write(line)
		
		print('Please reload the file in chaotica to ensure you specified the correct iterators to link!')
		exit(0)
		
	else:
		
		mode = 'using'
		term = input('Link how?  [copy=from,to OR using=a,b,c] => ')
		onlyUse = [x for x in term[term.index('=')+1:].strip().split(',')]
		
		if 'copy' in term:
			posFrom = int(onlyUse[0])-1
			posTo = int(onlyUse[1])-1
			
			weightvals[posTo] = weightvals[posFrom]
			for i, element in enumerate(weightvals):
				if i == posFrom or i == posTo: continue
				else:
					weightvals[i][posTo] = weightvals[i][posFrom]
					
			for j in weightvals:
				print(j)
			
		onlyUse = ['Iterator ' + str(x) for x in onlyUse]
		print('Using', onlyUse)
		
		with open(filename.replace('.chaos', '_xaosed.chaos'), 'w') as f:
			
			iterOn = 0
			numWeights = len(contents)
			
			lines = [None if 'per_iterator_weights' in x else x for x in lines]
			lines = [x for x in lines if not isWeight(x)]
			
			for line in lines:
				if line is None:
					f.write('\t\t\t\t\t<node name="per_iterator_weights">\n')
					for i, weight in enumerate(weightvals[iterOn-1]):
						lineval = '\t\t\t\t\t\t'
						lineval += '<real name="Iterator '
						lineval += str(i+1)
						lineval += ' weight">'
						
						if 'copy' in term:
							lineval += weight
						else:
							if 'Iterator ' + str(iterOn) in onlyUse:
								if 'Iterator ' + str(i+1) in onlyUse:
									lineval += '1'
								else:
									lineval += '0'
							else:
								if 'Iterator ' + str(i+1) in onlyUse:
									lineval += '0'
								else:
									lineval += weight
							
						
						lineval += '</real>\n'
						f.write(lineval)
				elif '<iterator name=' in line:
					iterOn += 1
					f.write('\t\t\t<iterator name="Iterator ' + str(iterOn) + '">\n')
				else:
					f.write(line)
		
				
if __name__ == '__main__':
	if not dirSearch(' '.join(sys.argv[1:]), modificationFunc):
		print('File was not found.')