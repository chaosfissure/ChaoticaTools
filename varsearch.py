import os
import sys

def dirSearch(searchterm):

	cwd = os.getcwd()
	
	d = os.listdir(os.getcwd())
	folders = [x for x in d if os.path.isdir(x)]
	files = [x for x in d if '.chaos' in x and not os.path.isdir(x)]
		
	for z in files:
		with open(z, 'r') as f:
			for line in f.readlines():
				lowerline = line.lower()
				if searchterm.lower() in lowerline and 'name' in lowerline and 'ifs' not in lowerline:
					a, b = os.path.split(os.getcwd())
					print b, '-', z, '-', '\t\t', line.lstrip().rstrip()
					break
		
	for folder in folders:
		os.chdir(os.path.join(cwd,folder))
		dirSearch(searchterm)
		os.chdir(cwd)
				
if __name__ == '__main__':		
	fname = None
	if len(sys.argv) > 1: 
		dirSearch(sys.argv[1])