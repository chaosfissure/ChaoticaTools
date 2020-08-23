import os
import sys
import copy

from collections import OrderedDict
from tkinter     import Tk


def clipboard_get():
	t = Tk()
	data = t.clipboard_get()
	t.destroy()
	return data
	
def clipboard_set(what):
		
	if os.name != 'nt':
		# I assume this works, but haven't tested it.
		t = tk()
		t.clipboard_clear()
		t.clipboard_append(what)
		t.destroy()
		
	else:
		# I can't just os.system(f'{what} | clip) because my
		# solution might have newlines or whitespace in it.
		# As a result, we're going to do the good ol' "make a
		# file and use it" approach.
	
		fname = '__tkinter_is_too_lazy__'
		with open(fname, 'w') as f:
			f.write(what)
		os.system(f'clip < {fname}') # Damn you tkinter
		os.remove(fname)


def ensure_xaos(parameters, len_xforms):
	if 'chaos' not in parameters:
		parameters['chaos'] = ' '.join(['1']*len_xforms)

def extract_xform_line(line):
	parameters = OrderedDict()
	line = line.replace('<xform', '').replace('/>', '').strip()
	
	while 1:
		equals = line.find('=')
		if equals == -1:
			break
			
		key       = line[:equals]
		
		val_start = line.find('"', equals+1)
		val_end   = line.find('"', val_start+1)
		value     = line[val_start+1 : val_end]
		
		line = line[val_end+1:].strip()
		
		parameters[key] = value
		
	return parameters
	
def inject_loop(xforms):
	# Inject a transform 0 and 1 ahead of all existing transforms.
	# Transform 0 points to transform 1.
	# Transform 1 points to the existing transforms.
	# Append the transforms.
	# Append another loop with a single linear transform.
	
	BLANK = extract_xform_line('<xform weight="0.5" color="0" linear="1" coefs="0 0 0 0 0 0" opacity="1" />')
	
	xf_zero = copy.deepcopy(BLANK)
	xf_one  = copy.deepcopy(BLANK)
	
	xf_zero['chaos'] = '0 1 ' + '0 '*len(xforms) + ' 1 0 '
	xf_one['chaos']  = '0 0 ' + '1 '*len(xforms) + ' 0 0 '
	
	for remaining_xform in xforms:
		remaining_xform['chaos'] = '0 0 ' + remaining_xform['chaos'] + ' 0 0'
		
	xf_minus_two = copy.deepcopy(BLANK)
	xf_minus_one = extract_xform_line('<xform weight="0.5" color="0" linear="1" coefs="1 0 0 1 0 0" opacity="1" />')
	
	xf_minus_two['chaos'] = '0 0 ' + '0 '*len(xforms) + ' 0 1 '
	xf_minus_one['chaos'] = '0 0 ' + '0 '*len(xforms) + ' 0 1 '
 		
	return [xf_zero, xf_one] + xforms + [xf_minus_two, xf_minus_one]
	

def xform_to_string(xform):
	kvp = ' '.join(f'{k}="{v}"' for k, v in xform.items())
	return f'<xform {kvp} />'
	
def xforms_to_string(xforms):
	return '\n'.join(xform_to_string(xform) for xform in xforms) + '\n'
	

if __name__ == '__main__':

	data = clipboard_get().split('\n')
	
	non_xforms = []
	xforms     = []
	
	THE_GOBBLEDEGOOK_STRING = '%%&$&__\\THIS_IS__ANTI_CLASHING_STRING__GO__FISH//__&$&%%'
	
	for line in data:
		if line.strip().startswith('<xform'):
			if not xforms:
				non_xforms.append(THE_GOBBLEDEGOOK_STRING)
			xforms.append(extract_xform_line(line))
		else:
			non_xforms.append(line)
		
	for elem in xforms:
		ensure_xaos(elem, len(xforms))
		
	xforms = inject_loop(xforms)	
	remade = '\n'.join(non_xforms).replace(THE_GOBBLEDEGOOK_STRING, xforms_to_string(xforms))
		
	clipboard_set(remade)
	
	
	
	
