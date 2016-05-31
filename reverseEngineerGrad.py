from Tkinter import Tk
import os
import sys
import random

def floatRGBToHSV(*args):
	
	r = g = b = 1.0
	if len(args) == 3:
		r = args[0]
		g = args[1]
		b = args[2]
		
	elif type(args[0]) is list or type(args[0]) is tuple:
		r = args[0][0]
		g = args[0][1]
		b = args[0][2]
	
	min = max = h = s = v = delta = 0.0
	
	if  r<=g and r<=b:
		min = r
		if g >= b: max = g
		else:      max = b
		
	elif g<=r and g<=b:
		min = g
		if r >= b: max = r
		else:      max = b
		
	else:
		min = b
		if r >= g: max = r
		else:      max = g

	v = max
	delta = max-min
	if max <= 0.0:
		s = h = 0.0
		
	else:
		s = delta/max
		if delta == 0.0:
			h = 1.0
		else:
			if r >= max:
				h = (g-b)/delta
			else:
				if (g >=max):
					h = 2.0 + ((b-r) / delta)
				else:
					h = 4.0 + ((r-g) / delta)
					
				h *= 60.0
				
		if h < 0:
			h += 360.0

	return [h/360.0, s, v]

	
def groupby(l, n):
	return [l[i:i+n] for i in xrange(0, len(l), n)]
	
def RGBFloatToInt(r, g, b):
	
	r = min(max(r, 0), 255)
	g = min(max(g, 0), 255)
	b = min(max(b, 0), 255)

	rVal = int(255.0 * r)
	gVal = int(255.0 * g) << 8
	bVal = int(255.0 * b) << 16

	return rVal+gVal+bVal
	
def approximateAndSimplify(rgbData):

	hsv = [ [i] + floatRGBToHSV(rgb) for i, rgb in enumerate(rgbData)]

	h_positions = [0]
	s_positions = [0]
	v_positions = [0]
	
	#Just because I'm lazy and can't use enums in python...
	pos,h,s,v = 0,1,2,3
	
	#Yeah, these have four entries even though HSV is three things, solely because the position is tacked on 
	#to this and to keep consistancy using up[h] or down[v] with hsv[element][h] and whatnot, it seems like a
	#simple way to do this.
	up = [False,False,False,False]
	down = [False,False,False,False]
	run = [0,0,0,0]
	smallValues = [hsv[0][pos],hsv[0][h],hsv[0][s],hsv[0][v]]
	
	minstep = 0.05
	
	itemOn = h
	while itemOn < 4:
		element = 0
		while element < len(hsv)-1:
		
			#Keep going until we reach the end, until we reach the last known element
			if (up[itemOn] and hsv[element][itemOn] < hsv[element+1][itemOn]) or (down[itemOn] and hsv[element][itemOn] > hsv[element+1][itemOn]):
				element += 1
				
			#If we go from up or down to flat, note the endpoint and negate that we're going in any direction
			elif (up[itemOn] or down[itemOn]) and hsv[element][itemOn] == hsv[element+1][itemOn]:
				
				if abs(smallValues[itemOn]-hsv[element][itemOn]) > minstep:
					# We're at an interesting position.
					up[itemOn] = False
					down[itemOn] = False
					
					# Record the endpoint.
					if itemOn == h:
						h_positions.append(element)
					elif itemOn == s:
						s_positions.append(element)
					else:
						v_positions.append(element)
						
					smallValues[itemOn] = hsv[element][itemOn]
					
				element += 1
			
			# If we're going flat at all...
			elif (not up[itemOn]) and (not down[itemOn]):
				# If we go to not being flat, find the midpoint and mark the edges too...
				if (hsv[element][itemOn]!= hsv[element+run[itemOn]+1][itemOn]):
				
					# If the length of the run is more than 1, there is a midpoint we need to use to flatten the curve.
					# And regardless of midpoints or not, we need to make note of the end.
					priorElement = hsv[element][itemOn]
					
					if itemOn == h:
						if run[h] > 1:
							h_positions.append((element+(element+run[h]))/2)
						h_positions.append(element+run[h])
						run[h] = 0
					elif itemOn == s:
						if run[s] > 1:
							s_positions.append((element+(element+run[s]))/2)
						s_positions.append(element+run[s])
						run[s] = 0
					else:
						if run[v] > 1:
							v_positions.append((element+(element+run[v]))/2)
						v_positions.append(element+run[v])
						run[v] = 0
						
					smallValues[itemOn] = hsv[element][itemOn]
					
					# Make sure to update to the element we're actually on now...
					element += (run[itemOn]+1)
					run[itemOn] = 0
					
					if hsv[element][itemOn] > priorElement:
						up[itemOn] = True
					else:
						down[itemOn] = True
					
				# Else we're still going flat...
				else:
					run[itemOn] += 1
					
			# Then we have our weird edge cases of oscillation back and forth.  Rather than actually
			# doing anything with it, we'll just switch going up and down.
			elif (down[itemOn] and hsv[element][itemOn] < hsv[element+1][itemOn]) or (up[itemOn] and hsv[element][itemOn] > hsv[element+1][itemOn]):
			
				if abs(smallValues[itemOn]-hsv[element][itemOn]) > minstep:
					
					priorElement = hsv[element][itemOn]
					
					if itemOn == h:
						h_positions.append(element)
					elif itemOn == s:
						s_positions.append(element)
					else:
						v_positions.append(element)
				
					down[itemOn] = not down[itemOn]
					up[itemOn] = not up[itemOn]
				
				element += 1
		

		if itemOn == h:
			h_positions.append(len(hsv)-1)
		elif itemOn == s:
			s_positions.append(len(hsv)-1)
		else:
			v_positions.append(len(hsv)-1)		
		itemOn += 1
					
	#checking for duplicates...
	
	duplicate_pos = []
	
	for i in range(len(h_positions)):
		if not (h_positions[i] in duplicate_pos):
			duplicate_pos.append(h_positions[i])
	h_positions = duplicate_pos
	
	duplicate_pos = []
	for i in range(len(s_positions)):
		if not (s_positions[i] in duplicate_pos):
			duplicate_pos.append(s_positions[i])
	s_positions = duplicate_pos
	
	duplicate_pos = []
	for i in range(len(v_positions)):
		if not (v_positions[i] in duplicate_pos):
			duplicate_pos.append(v_positions[i])
	v_positions = duplicate_pos
						
	points = []
	data = []
	for valuetype in [h_positions, s_positions, v_positions]:
		for pos in valuetype:
			if pos in points: continue
		
			points.append(pos)
			data.append([pos] + rgbData[pos])
	
	return data


def extract_gradient(chaosData):

	values = []
	
	try:
	
		useline = None
		splitlines = chaosData.split('\n')
		
		
		for i, line in enumerate(splitlines):
			if '<table name="flam3_palette">' in line:
				useline = None if i==len(splitlines)-1 else splitlines[i+1].lstrip().rstrip()
				break
				
		if useline is not None:
			useline = useline.replace('<values>', '')
			useline = useline.replace('</values>', '')
										
			values = groupby([float(value) for value in useline.split(' ')], 3)
		
			print values
		
	except:
		print 'Error.  Unable to find Chaos data in clipboard.'
		exit()
			

	# Construct UF format...
	z = 'Gradient-Fractal1,Background {\n'
	z += 'gradient:\n'
	z += '  title="Extracted" smooth=yes rotation=1\n  '
	
	# Insert gradient here.
	
	chaoticaAppend = 1.0/256.0
	
	hsvdata = approximateAndSimplify(values)
	
	for pos, r, g, b in hsvdata:	
		position = int((400.0*pos)/256.0)
		color = RGBFloatToInt(r, g, b)
		indexStr = 'index='+str(position)
		colorStr = 'color='+str(color)
		z += ' ' + indexStr + ' ' + colorStr
		
	z += '\n'
	z += 'opacity:\n'
	z += 'smooth=yes index=0 opacity=255\n'
	z += '}\n'
	
	return z

if __name__ == '__main__':	
	r = Tk()
	r.withdraw()
	clipboard = r.clipboard_get()
	gradient = extract_gradient(clipboard)	
	r.clipboard_append(gradient)
		