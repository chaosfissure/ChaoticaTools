from tkinter import Tk
import os
import sys
import random

def isCorrect(filename,directory):
	return input('\nIs ' + filename + ' in ' + directory + ' the correct file? (y/n) =>').lower() == "y"

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
	
	folders.sort(key=os.path.getmtime, reverse=True)
		
	for f in files:
		if ignoreCaseCount(f,searchterm) and isCorrect(f, os.getcwd()):
			modifyChaosFile(os.path.join(os.getcwd(), f), colordata)
			return True
							
	cwd = os.getcwd()
	longest = 0
	for folder in folders:
		longest = max(len(folder), longest)
		print("\rSearching in", folder, ' '*longest, end='')
		os.chdir(os.path.join(cwd,folder))
		result = dirSearch(searchterm, colordata)
		os.chdir(cwd)
		if result: return True
			
	return False
	
	
def FromApoParam(clipboard):
	
	foundPaletteStart = foundDataLines = False

	if (clipboard.count('<palette count="256" format="RGB">\n') == 0):
		print("Erroneous pasted data!  Needs palette information.  Aborting!!")
		exit(0)
		
	paletteTerm    = '<palette count="256" format="RGB">\n'	
	startLoc       = clipboard.index(paletteTerm) + len(paletteTerm)
	endLoc         = clipboard.index('</palette>')
	relevantString = clipboard[startLoc:endLoc]

	paletteLines = [x.lstrip().rstrip() for x in relevantString.split('\n')]

	colorString = ''
	
	with open('foo.txt', 'w') as f:
		for line in paletteLines:
			while len(line) > 0:
				hexval = line[:6]
				line = line[6:]
			
				intValue = int(hexval,16)
				r = ((intValue >> 16) & 255) / 255.0
				g = ((intValue >> 8)  & 255) / 255.0
				b = (intValue         & 255) / 255.0
				colorString += f' {r} {g} {b}'
			
				f.write(f'vec3({r:5>.3f}, {g:5>.3f}, {b:5>.3f})\n')
			
	return colorString.strip()
	
def FromUGR(clipboard):

	colorLines  = [line.strip() for line in clipboard.split('\n') if 'index=' in line and 'color=' in line]
	colorString = [None for _ in range(256)]
	last_color  = None
	last_idx    = 0
	
	for line in colorLines:
	
		idx, color = [int(x.split('=')[1]) for x in line.split(' ')]
		
		r = ( color        & 255) / 255.0
		g = ((color >> 8)  & 255) / 255.0
		b = ((color >> 16) & 255) / 255.0
		
		# Index is from 0 to 400, not 0 to 256
		idx = int(round(256*idx / 400))
		
		# Default to initial color
		if last_color is None:
			last_color = f' {r} {g} {b}'
		
		# Update all terms between last color and this entry
		# with the previous color.
		for j in range(last_idx, idx+1):
			colorString[j] = last_color
		
		# Now we move to the current color and index.
		last_color = f' {r} {g} {b}'
		last_idx   = idx
			
	for j in range(last_idx, 256):
		colorString[j] = last_color
			
	return ' '.join(colorString).strip()


if __name__ == '__main__':
	
	# What are we looking for?
	searchFor = None
	if len(sys.argv) > 1: searchFor = ' '.join(sys.argv[1:])
	if searchFor is None: searchFor = input('Search for what filename? -> ')
	
	# Get Tkinter stuff for clipboard
	r = Tk()
	r.withdraw()
	clipboard = r.clipboard_get()

	#parse contents.
	if clipboard.startswith('<flame name'):
		colorString = FromApoParam(clipboard)
	else:
		colorString = FromUGR(clipboard)
	
	dirSearch(searchFor, colorString)