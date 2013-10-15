"""
**********************************************************************
xyzmfcc.py

Copyright (C) 2013 Casper Steinmann

This file is part of the FragIt project.

FragIt is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

FragIt is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301, USA.
***********************************************************************/
"""
from numpy import sqrt, dot, where, array
from writer import Standard
from util import WriteStringToFile

from util import file_extension,is_list,listTo2D,join2D,is_int
from util import listToRanges,listOfRangesToString,Uniqify,ravel2D
from util import deepLength,listDiff,intlistToString
from util import getFilenameAndExtension
from util import shares_elements, calculate_hydrogen_position

from mfcc import MFCC, Cap

class XYZMFCC(Standard):
    def __init__(self, fragmentation):
        Standard.__init__(self,fragmentation)
        self._mfcc = MFCC(fragmentation)

    def setup(self):
        self._setupLayeredInformation()
        self._setupActiveFragmentsInformation()
        #self._validateMultiLayerInformation()
        if self._do_pymol: self._dump_pymol()
        if self._do_jmol: self._dump_jmol()

    def _setupLayeredInformation(self):
        self._fragment_layers = self._getFragmentLayersFromFragment()

    def _getFragmentLayersFromFragment(self):
        fragments = self._fragmentation.getFragments()
        return array([1 for i in fragments])

    def _setupActiveFragmentsInformation(self):
        self._active_atoms = []

    def _dump_pymol(self):
        from pymol import PymolTemplate
        pt = PymolTemplate(self._input_filename, self._output_filename)
        self._setTemplateData(pt)
        self._writeTemplateFile(pt)

    def _dump_jmol(self):
        from jmol import JmolTemplate
        pt = JmolTemplate(self._input_filename, self._output_filename)
        self._setTemplateData(pt)
        self._writeTemplateFile(pt)

    def _setTemplateData(self, template):
        template.setFragmentsData(self._fragmentation.getFragments())
        template.setBufferData(self._fragment_layers)
        template.setActiveData(self._active_atoms)
        template.setBackboneData(self._fragmentation.getBackboneAtoms())
        template.setPairData(self._fragmentation.getExplicitlyBreakAtomPairs())

    def _writeTemplateFile(self, template):
        template.override()
        template.write()

    def _build_single_fragment(self, fragment, caps):
        atoms = [self._fragmentation.getOBAtom(i) for i in fragment]
        nucz  = [a.GetAtomicNum() for a in atoms]
        neighbours = [-1 for a in atoms]
        ids = [i for i in fragment]

        for icap,cap in enumerate(caps):
            if shares_elements( fragment, cap.getAtomIDs() ):
                for id,atom,z,nbr in zip(cap.getAtomIDs(), cap.getAtoms(), cap.getNuclearCharges(), cap.getNeighbourList() ):
                    if id not in fragment:
                        atoms.append( atom )
                        nucz.append( z )
                        neighbours.append( nbr )
                        ids.append( id )

        return Cap(atoms, ids, nucz, neighbours)

    def BuildFragment(self, fragment):
        return self._build_single_fragment(fragment, self._mfcc.getCaps())

    def _fragment_xyz(self, fragment ):
        """Generates the xyz file format based on the atoms, types,
           ids and neighbours of each fragment
        """
        # NB! the word fragment here is actually of type Cap. Just to be sure
        # nobody is actually doing something utterly wrong, check that here.
        if not type(fragment) == Cap: raise ValueError("_fragment_xyz expected an object of type Cap.")
        atoms = fragment.getAtoms()
        nuczs = fragment.getNuclearCharges()
        nbrls = fragment.getNeighbourList()
        n = len(atoms)
        s = "%i\n%s\n" % (n,"")
        for id, (atom, nucz, neighbour) in enumerate(zip(atoms,nuczs,nbrls)):
            (x,y,z) = (atom.GetX(), atom.GetY(), atom.GetZ())
            if atom.GetAtomicNum() != nucz:
                # atom is the light atom and it is connected to the nbrs[id] atom
                heavy_atom = self._fragmentation.getOBAtom( neighbour )
                (x,y,z) = calculate_hydrogen_position( heavy_atom, atom )
            s += "%s %20.12f %20.12f %20.12f\n" % (self._elements.GetSymbol(nucz),
                                                   x, y, z)
        return s

    def writeFile(self, filename):
        """Dumps all caps and capped fragments to individual files
        """
        ff,ext = getFilenameAndExtension(filename)
        filename_template = "{0}_{1}_{2:03d}{3}"

        # these are the capped fragments
        for ifg,fragment in enumerate(self._fragmentation.getFragments()):
            capped_fragment = self.BuildFragment( fragment )
            ss = self._fragment_xyz( capped_fragment )
            with open( filename_template.format(ff, "fragment", ifg, ext), 'w' ) as f:
                f.write(ss)

        # these are the caps
        for icap, cap in enumerate( self._mfcc.getCaps() ):
            ss = self._fragment_xyz( cap )
            with open( filename_template.format(ff, "cap", icap, ext), 'w' ) as f:
                f.write(ss)
