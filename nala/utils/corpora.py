import os
from nala.bootstrapping.iteration import Iteration
from nalaf.utils.readers import VerspoorReader, TmVarReader, SETHReader
from nalaf.utils.annotation_readers import SETHAnnotationReader
from nalaf.structures.data import Dataset

#Var = Variome
#Var120 = Variome_120
#?A = Abstracts only
#?F = Full Text only
ALL_CORPORA = [
'tmVar', 'MF', 'SETH', 'OMM', 'OSIRIS', 'SNPC',
'IDP4', 'IDP4A', 'IDP4F', 'nala', 'IDP4+',
'Var', 'VarA', 'VarF', 'Var120', 'Var120A', 'Var120F']

__corpora_folder = os.path.abspath("resources/corpora")

def get_corpus(name):
    if name == "tmVar":
        entirecorpusfile = os.path.join(__corpora_folder, 'tmvar', 'corpus.txt')
        return TmVarReader(entirecorpusfile).read()
    if name == "SETH":
        ret = SETHReader(os.path.join(__corpora_folder, 'seth', 'corpus.txt')).read()
        annreader = SETHAnnotationReader(os.path.join(__corpora_folder, 'seth', 'annotations'))
        annreader.annotate(ret)
        return ret
    elif name == "IDP4":
        return Iteration.read_IDP4()
    elif name == "nala":
        return Iteration.read_nala()
    elif name == "IDP4+":
        return Iteration.read_IDP4Plus()
    elif name == "Var":
        folder = os.path.join(__corpora_folder, 'variome', 'data')
        return VerspoorReader(folder).read()
    elif name == "Var120":
        folder = os.path.join(__corpora_folder, 'variome_120', 'annotations_mutations_explicit')
        return VerspoorReader(folder).read()
    elif name in ALL_CORPORA:
        return Dataset()
        #raise NotImplementedError("My bad, not implemented: " + name)
    else:
        raise Exception("Do not recognize given corpus name: " + name)
