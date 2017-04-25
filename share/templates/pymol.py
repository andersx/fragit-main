from pymol import stored

$FRAGMENTS
$BUFFER
$ACTIVE
$BACKBONE
$FRAGMENTQ

def atom_data_to_lists(l):
  lists = list()
  if len(l) == 0: return []
  fraglists = l.split(":")
  for fraglist in fraglists:
    atmlists = fraglist.split(",")
    lists.append(map(int, atmlists))
  return lists

def fragment_data_to_list(l):
  if len(l) == 0: return []
  fragment_properties = map(int, l.split(","))
  return fragment_properties

def select_fragment_by_id(id):
  fragments = atom_data_to_lists(fragments_data)
  idx = int(id)-1
  selection = "select fragment-%03i, none" % (idx+1)
  string = "".join([" or id %i" % atom for atom in fragments[idx]])
  cmd.do(selection + string)

def select_backbone():
  select_region("backbone", backbone_data)

def flatten_list(list_to_flatten):
  flat_list = []
  for items in list_to_flatten:
    flat_list.extend(items)
  return flat_list

def select_active_region():
  select_region("active", active_data)

def select_buffer_region():
  select_region("buffer", buffer_data)

def select_frozen_region():
  all_atoms = flatten_list(atom_data_to_lists(fragments_data))
  buffer_atoms = flatten_list(atom_data_to_lists(buffer_data))
  if len(buffer_atoms) == 0: return
  frozen_atoms = []
  for atom in all_atoms:
    if atom not in buffer_atoms:
      frozen_atoms.append(atom)
  frozen_data = ",".join(map(str,frozen_atoms))
  select_region("frozen", frozen_data)

def select_region(type, data, cut=40):
  atoms = flatten_list(atom_data_to_lists(data))
  if len(atoms) == 0: return
  selection_string = "select sele-%s, %s"
  sel_name = "none"
  while len(atoms) > 0:
    t_atoms = atoms[:cut]
    atoms = atoms[cut:]
    selection = selection_string % (type, sel_name)
    string = "".join([" or id %i" % atom for atom in t_atoms])
    cmd.do(selection + string)
    sel_name = "sele-%s" % type

def make_selection(type="fragment", id="1"):
  if type=="fragment" or type=="fid":
    select_fragment_by_id(id)
  elif type=="backbone" or type=="bb":
    select_backbone()
  elif type=="active":
    select_active_region()
  elif type=="buffer":
    select_buffer_region()
  elif type=="frozen":
    select_frozen_region()
  else:
    cmd.do("select sele, none")

def make_fragment_selections():
  fragments = atom_data_to_lists(fragments_data)
  for i,fragments in enumerate(fragments):
    select_fragment_by_id("%i" % (i+1))
  cmd.do("group fragments, fragment-*")

def make_selections():
  make_selection("active")
  make_selection("buffer")
  make_selection("frozen")
  select_backbone()
  make_fragment_selections()
  cmd.do("group selections, sele-*")

def color_selection(sel="all", color="green"):
  cmd.color(color, sel)

def color_atoms(data, color="green"):
  selection = "all"
  for d in data:
    sel = selection + " and id %i" % (d)
    color_selection(sel, color)

def hex_to_float(value):
  (ri,gi,bi) = hex_to_rgb(value)
  r = ri / 255.0
  g = gi / 255.0
  b = bi / 255.0
  return (r,g,b)

def hex_to_rgb(value):
  value = value.lstrip('#')
  lv = len(value)
  return tuple(int(value[i:i+2], 16) for i in [0, 2, 4])

def get_colors_for_fragments(list_of_fragments):
  color_names = ["color1", "color2", "color3", "color4", "color5", "color6", "color7", "color8", "color9", "color10"]
  colors_hex = ["#006837", "#1A9850", "#66BD63", "#A6D96A", "#D9EF8B", "#F46D43", "#ED5D3C", "#E0422F", "#D73027", "#A50026"]
  for c,n in zip(colors_hex, color_names):
      (r,g,b) = hex_to_float(c)
      cmd.do("set_color %s, [%3.1f, %3.1f, %3.1f]" % (n,r,g,b))
  col = color_names[:]
  while len(col) < len(list_of_fragments):
    col.extend(color_names)
  return col

def color_all_fragments():
  frags = atom_data_to_lists(fragments_data)
  colors = get_colors_for_fragments(frags)
  for i,atomlist in enumerate(frags):
    color_atoms(atomlist, colors[i])

def color_fragments_by_charge():
  """ Colors fragments by charges """
  charges = fragment_data_to_list(fragment_charges)
  fragments = atom_data_to_lists(fragments_data)
  for i, (fragment, charge) in enumerate(zip(fragments, charges)):
    if charge == -1:
      color_atoms(fragment, "red")
    elif charge == +1:
      color_atoms(fragment, "blue")
    else:
      color_atoms(fragment, "white")

def color_fragments(sele="fragments"):
  """ PyMOL GUI coloring function

      This function is invoked by the 'ColorFragments' option
      in the PyMOL user interface.
  """
  cmd.bg_color("white")
  if sele == "fragments":    
    color_all_fragments()

  elif sele == "buffer" or sele == "layers":
    cmd.do("color gray, sele-frozen")
    cmd.do("color marine, sele-buffer")

  elif sele == "active":
    cmd.do("color gray, sele-frozen")
    cmd.do("color marine, sele-buffer")
    cmd.do("color raspberry, sele-active")

  elif "charge" in sele:
    color_fragments_by_charge()

def calculate_center(list_of_coords):
  n = len(list_of_coords)
  X = 0.0
  Y = 0.0
  Z = 0.0
  for (x,y,z) in list_of_coords:
    X += x
    Y += y
    Z += z

  X /= n
  Y /= n
  Z /= n

  return X,Y,Z

# iterate over atoms in a fragment
def name_all_fragments():
  cmd.do("set label_size, 18")
  frags = atom_data_to_lists(fragments_data)
  for i,atms in enumerate(frags):
    stored.frgcrds=[]
    for atom in atms:
      selection = "all and id %i " % atom
      cmd.iterate_state(1, selector.process(selection), "stored.frgcrds.append([x,y,z])")
    (X,Y,Z) = calculate_center(stored.frgcrds)
    cmd.do("pseudoatom lbl-frag%i, pos=[%f,%f,%f]" % (i,X,Y,Z))
    cmd.do("label lbl-frag%i, \"Frag-%i\"" % (i,i+1))
  cmd.do("group labels, lbl-*")
  stored.did_labels = True

def name_fragments(action="show"):
  if action == "show":
    name_all_fragments()

def setup_rendering_defaults():
  cmd.do("set antialias, 2")
  cmd.do("set ray_trace_mode, 1")
  cmd.do("set ray_shadow, off")

# default commands we need to execute
# to set up the environment correctly
stored.did_labels = False
$LOADCOMMAND

color_fragments("fragments")
if len(atom_data_to_lists(fragments_data)) < 50:
  name_all_fragments()
make_selections()

cmd.do("show sticks, all")
cmd.do("select sele, none")
cmd.extend("NameFragments", name_fragments)
cmd.extend("ColorFragments", color_fragments)
cmd.extend("SelectFragments", make_selection)

setup_rendering_defaults()