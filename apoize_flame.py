import argparse
import math
import os

from collections import OrderedDict
from textwrap    import dedent
from xml.etree   import ElementTree


def clamp(val, fromwhat=0, towhat=1):
	if val < fromwhat: return fromwhat
	if val > towhat:   return towhat
	return val

def find_by_name(node, tag, name, dtype='infer'):
	''' Finds any child of `node`, with a given `tag` that has a specified `name` parameter. '''
	
	for child in node.findall(f'.//{tag}'):
		if name == child.attrib['name']:
		
			# Automagic type inference
			if dtype == 'infer':
				try:
					return int(child.text)
				except:
					try:    return float(child.text)
					except: pass
					
			# User supplied conversion
			elif dtype is not None:
				return dtype(child.text)
				
			# Fallback to string value
			return child.text
			
	raise ValueError(f'Not found: tag={tag}, name={name}')
			

class TransformGeom():

	@staticmethod
	def get_xy_for_arm(length, angle):
		angle      = (math.pi / 180.0) * angle
		y_sin_comp = math.sin(angle) * length
		x_cos_comp = math.cos(angle) * length
		return x_cos_comp, y_sin_comp

	def __init__(self, node):
		self.center = [float(x) for x in find_by_name(node, 'vec2', 'offset', None).split()]
		x_ang = find_by_name(node, 'real', 'x_axis_angle') % 360
		y_ang = find_by_name(node, 'real', 'y_axis_angle') % 360
		x_len = find_by_name(node, 'real', 'x_axis_length')
		y_len = find_by_name(node, 'real', 'y_axis_length')
		self.x_arm = TransformGeom.get_xy_for_arm(x_len, x_ang)
		self.y_arm = TransformGeom.get_xy_for_arm(y_len, y_ang)
		
	def __str__(self):
		# X, Y, Origin
		numbers = [*self.x_arm, *self.y_arm, *self.center]
		return ' '.join(f'{x:.3f}' for x in numbers)
		

class Xform():
	def __init__(self, node):
		self.params = {}
		for elem in node.find('.//params'):
			val = float(elem.text)
			if val != 0:
				self.params[elem.attrib['name']] = val
			
		# Some replacements of terms for convenience
		
		if 'gaussian' in self.params:		
			# Negating the value means the blur will still exist even if another
			# transform has a high positive value.
			#
			# I also like noise better than gaussian_blur.
			self.params['noise'] = -self.params.pop('gaussian')
			
		if 'radial_gaussian' in self.params:
			self.params['radial_blur'] = -self.params.pop('radial_gaussian')
			
			
		#if len(self.params) == 0 and 'noise' in self.params:
			#self.params.clear()
		
		
		
class Coloring():
	def __init__(self, node):
		
		self.opacity  = 1
		self.color    = 0
		self.symmetry = 1
		
		flam3_shader  = node.find('.//flam3_shader')
		if flam3_shader is not None:
			self.opacity  = find_by_name(flam3_shader, 'real',       'opacity')
			self.color    = find_by_name(flam3_shader, 'real', 'palette_index')
			self.symmetry = find_by_name(flam3_shader, 'real',   'blend_speed')

			# Okay, chaotica uses linear interpolation from [0,1].
			#
			# Apo goes from [-1, 1], but also negates this so `+1` is the
			# original color, while `-1` is the target color.
			# 
			# What the heck?
			self.symmetry = -2*(self.symmetry-0.5)
			
			# Clamp values since chaotica can oversatuate but Apo cannot.
			self.opacity  = clamp(self.opacity)
			self.color    = clamp(self.color)
			self.symmetry = clamp(self.symmetry, -1, 1)
			
		
	def __str__(self):
		return ' '.join(f'{k}="{v:.3f}"' for k,v in {
			'color'    : self.color,
			'symmetry' : self.symmetry,
			'opacity'  : self.opacity,
		}.items())
		
class ChaoticaIterator():
	
	def __init__(self, node):
	
		self.affines = {}
		for elem in node.findall('.//affine2'):
			self.affines[elem.attrib['name']] = TransformGeom(elem)
	
		# Chaotica seems to always order the iterators based on how they manifest
		# in its world editor. Hopefully this is true, so I don't need to sort the
		# iterators strictly by name and try reordering everything to account for
		# weird degenerate cases.
		
		# I hope chaotica always generates them ordered instead of me needing to
		# strictly order them based on the name of the weight in the xml...
		
		try:
			self.weight = find_by_name(node.find('.//weights_selector'), 'real', 'base_weight') # Global scalar for this xform
		except:
			# Probably the final/camera transform
			self.weight = 0.5
			
		try:
			self.weights = ' '.join(x.text for x in node.findall('.//weights_selector/node/real')) # "Xaos"			
		except:
			# Probably the final/camera transform
			self.weights = ''

		# Just assume normal transforms now since apo doesn't inherently have
		# the same pre/post structure that chaotica does.
		self.transforms = []
		for xf_node in node.findall('.//flam3_variation'):
			self.transforms.append(Xform(xf_node))
			
		# Last but not least, the coloring
		self.coloring = Coloring(node)
			
	def __str__(self):
		
		transform_str = ' '.join(f'{k}="{v}"'
			for transform in self.transforms
				for k, v in transform.params.items())
										
		affine_txt = ''
		for k, v in self.affines.items():
			prefix = ('post', 'coefs')['pre' in k.lower()]
			affine_txt += f'{prefix}="{v}" '
	
		return f'<xform weight="{self.weight:.6f}" {self.coloring} {transform_str} {affine_txt} chaos="{self.weights}" />'
				
			
class ChaoticaIterators():
	def __init__(self, root_node):
	
		# Normal transforms
		self.iterators = [ChaoticaIterator(node) for node in root_node.findall('.//node/iterator')]
					
		# Final transform
		fx = root_node.find('.//camera/flam3_transform')
		if fx: self.final_transform = ChaoticaIterator(fx)
		else:  self.final_transform = ''
		
	def __str__(self):
		final_xform_str = str(self.final_transform).replace('xform', 'finalxform')
		return '\n'.join(map(str, (*self.iterators, final_xform_str)))

class ImagingSettings():
	def __init__(self, root_node):
		imaging = root_node.find('imaging')
		
		width           = find_by_name(imaging, 'int', 'image_width' )
		height          = find_by_name(imaging, 'int', 'image_height')
		self.size       = (width, height)
		self.brightness = round(find_by_name(imaging, 'real',  'brightness'), 3)
		self.gamma      = round(find_by_name(imaging, 'real', 'flam3_gamma'), 3)
		
		camera = root_node.find('.//camera')

		# Okay, I can understand using radians instead of degrees, but why do chaotica and
		# apo have different rotation signs!?
		self.rotation = find_by_name(camera, 'real', 'rotate')
		self.rotation = -(self.rotation%360) * (math.pi / 180.0)
		
		# Also, why does apo XML show `scale` while the GUI uses `scale/6` ???
		# Why does chaotica use 100 over this value?
		self.scale    = 1.0 / (find_by_name(camera, 'real', 'sensor_width') / 100.0) * 6
		
		# Although Apo seems to transparently negate y values in the GUI for most things,
		# it apparently isn't negated for the main viewing offset compared to chaotica.
		self.camera_pos     = [float(x) for x in find_by_name(camera, 'vec2', 'pos').split()]
		self.camera_pos[1] *= -1

		
class Gradient():

	@staticmethod
	def to_rgb_tuples(node):
		values = [float(x) for x in node.text.split()]
		if len(values) % 3 != 0:
			raise ValueError(f'Weird gradient format has {len(values)} entries instead of something divisible by 3.')	
		for i in range(0, len(values), 3):
			rgb = values[i:i+3]
			rgb = [min(255, max(0, int(x*255))) for x in rgb]
			yield ''.join(hex(elem)[2:].rjust(2, '0') for elem in rgb).upper()
			
			
	@staticmethod
	def eight_entry_buckets(node):
		collect = []
		for elem in Gradient.to_rgb_tuples(node):
			collect.append(elem)
			if len(collect) == 8:
				yield ''.join(collect)
				collect.clear()
					

	def __init__(self, root_node):
		color = root_node.find('.//colouring/table/values')
		if color is None:
			raise ValueError('This only supports chaotica fractals using gradient-based palettes')
		self.palette = list(Gradient.eight_entry_buckets(color))
		
		
	def __str__(self):
		grad_part = '\n\t'.join(self.palette)
		return f'''
<palette count="256" format="RGB">
	{grad_part}
</palette>
		'''
		
		
def make_flame_from(node):

	gradient = Gradient(node)
	iters    = ChaoticaIterators(node)
	imaging  = ImagingSettings(node)
		
	prop = OrderedDict()
	prop['name']              = 'Chaotica Import'      # Iunno if using the actual chaotica filname would be better
	prop['version']           = 'Not Really Apophysis' # This statement is true
	prop['size']              = ' '.join(map(str, imaging.size)) # This fortunately is the same
	prop['center']            = ' '.join(map(str, imaging.camera_pos)) # See `ImagingSettings`
	prop['scale']             = round(imaging.scale, 3)    # See `ImagingSettings`
	prop['angle']             = round(imaging.rotation, 3) # See `ImagingSettings`
	prop['oversample']        = 1       # Overwritten by actual render settings, no purpose
	prop['filter']            = 0.5     # Overwritten by actual render settings, no purpose
	prop['quality']           = 50      # Overwritten by actual render settings / gui density selection, no purpose
	prop['background']        = '0 0 0' # Not bothering to port this value
	prop['brightness']        = round(imaging.brightness, 3)
	prop['gamma']             = round(imaging.gamma,      3)
	prop['gamma_threshold']   = 0   # Not bothering to port this value
	prop['estimator_radius']  = 9   # Does nothing on 7x
	prop['estimator_minimum'] = 0   # Does nothing on 7x
	prop['estimator_curve']   = 0.4 # Does nothing on 7x
	prop['enable_de']         = 0   # Does nothing on 7x
	prop['plugins']           = ''  # Not sure what this does
	prop['new_linear']        = 1	# Probably worth having
	
	prefix  = ' '.join(f'{k}="{v}"' for k,v in prop.items())
	iterstr = str(iters).replace('\n', '\n\t')
	gradstr = str(gradient).replace('\n', '\n\t')
	
	return dedent(f'''
<flame {prefix}>
	{iterstr}
	{gradstr}
</flame>
''')

if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument('input', help='Input chaos file')
	ap.add_argument('-o', '--output', required=True, help='output file with a single flame to copypasta into apo')
	args = ap.parse_args()
	
	tree = ElementTree.parse(args.input)
	root = tree.getroot().find('.//IFS')
	txt  = make_flame_from(root)
	
	with open(args.output, 'w') as f:
		f.write(txt)
	
