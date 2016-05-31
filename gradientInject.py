from Tkinter import Tk
import os
import sys
import random

def isCorrect(filename,directory):
	return raw_input('Is ' + filename + ' in ' + directory + ' the correct file? (y/n) =>').lower() == "y"

def ignoreCaseCount(searchInThisString,searchForTerm):
	return searchForTerm.lower() in searchInThisString.lower()

def modifyChaosFile(filename, colordata):

	lines = []
	
	with open(filename, 'r') as f:	
		ignoreColoringXML = False
		for line in f.readlines():
			if '<colouring>' in line:
				ignoreColoringXML = True
				lines.append(line)
			if '</colouring>' in line and ignoreColoringXML:
				lines.append('\t\t\t<table name="flam3_palette">\n')
				lines.append('\t\t\t\t<values>' + colordata + '</values>\n')
				lines.append('\t\t\t</table>\n')
				lines.append('\t\t</colouring>\n')
				ignoreColoringXML = False
			elif ignoreColoringXML:
				continue
			else:
				lines.append(line)
				
	with open(filename.replace('.chaos', '_gradiated.chaos'), 'w') as f:
		for line in lines:
			f.write(line)
			
def dirSearch(searchterm, colordata):

	ls = os.listdir(os.getcwd())
	folders = [x for x in ls if os.path.isdir(x)]
	files   = [x for x in ls if x.endswith('.chaos') and not os.path.isdir(x)]
		
	for f in files:
		if ignoreCaseCount(f,searchterm) and isCorrect(f, os.getcwd()):
			modifyChaosFile(os.path.join(os.getcwd(), f), colordata)
			return True
							
	cwd = os.getcwd()
	for folder in folders:
		print "Searching in", folder
		os.chdir(os.path.join(cwd,folder))
		result = dirSearch(searchterm, colordata)
		os.chdir(cwd)
		if result: return True
			
	return False


if __name__ == '__main__':
	
	# What are we looking for?
	searchFor = None
	if len(sys.argv) > 1: searchFor = ' '.join(sys.argv[1:])
	if searchFor is None: searchFor = raw_input('Search for what filename? -> ')
	
	# Get Tkinter stuff for clipboard
	r = Tk()
	r.withdraw()
	clipboard = r.clipboard_get()

	#parse contents.
	foundPaletteStart = foundDataLines = False

	if (clipboard.count('<palette count="256" format="RGB">\n') == 0):
		print "Erroneous pasted data!  Needs palette information.  Aborting!!"
		exit()
		
	paletteTerm    = '<palette count="256" format="RGB">\n'	
	startLoc       = clipboard.index(paletteTerm) + len(paletteTerm)
	endLoc         = clipboard.index('</palette>')
	relevantString = clipboard[startLoc:endLoc]

	paletteLines = [x.lstrip().rstrip() for x in relevantString.split('\n')]
	print paletteLines

	colorString = ''
	for line in paletteLines:
		while len(line) > 0:
			hexval = line[:6]
			line = line[6:]
			
			intValue = int(hexval,16)
			r = ((intValue >> 16) & 255) / 255.0
			g = ((intValue >> 8)  & 255) / 255.0
			b = (intValue         & 255) / 255.0
			
			colorString += ' ' + ' '.join(map(str, [r, g, b]))
			
	dirSearch(searchFor, colorString.lstrip().rstrip())