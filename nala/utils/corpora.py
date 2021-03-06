import os
from nala.utils import nala_repo_path
from nala.utils import MUT_CLASS_ID
from nala.bootstrapping.iteration import Iteration
from nalaf.utils.readers import VerspoorReader, TmVarReader, OSIRISReader, MutationFinderReader, \
    PMIDReader, HTMLReader, ProteinResidueCorpusPartialReader
from nalaf.utils.annotation_readers import DownloadedSETHAnnotationReader, AnnJsonAnnotationReader
from nalaf.structures.data import Dataset
from nalaf import print_verbose, print_debug

# Var = Variome
# Var120 = Variome_120
# ?A = Abstracts only
# ?F = Full Text only
ALL_CORPORA = [
    'MF', 'OMM', 'OSIRIS', 'SNP', 'LEAP-FS',
    'SETH',
    'tmVar',
    'Var', 'VarA', 'VarF',
    'Var120', 'Var120A', 'Var120F',
    'IDP4', 'IDP4A', 'IDP4F',
    'nala', 'nala_training', 'nala_test',
    'IDP4+',
    'nala_random'
]

__corpora_folder = nala_repo_path(["resources", "corpora"])


def get_corpora(names, only_class_id=None):
    dataset = Dataset()

    for name in names.split(','):
        dataset.extend_dataset(get_corpus(name, only_class_id=only_class_id))

    return dataset


def get_corpus(name, only_class_id=None, hdfs_url=None, hdfs_user=None):
    if (name.startswith(os.sep) or name.endswith(os.sep)):
        return get_annjson_corpus(name, only_class_id=only_class_id, hdfs_url=hdfs_url, hdfs_user=hdfs_user)
    else:
        return get_corpus_name(name, only_class_id=only_class_id)


def get_annjson_corpus(folder, only_class_id=None, hdfs_url=None, hdfs_user=None):
    ret = HTMLReader(folder, whole_basename_as_docid=True, hdfs_url=hdfs_url, hdfs_user=hdfs_user).read()
    AnnJsonAnnotationReader(folder, read_only_class_id=only_class_id, whole_basename_as_docid=True, hdfs_url=hdfs_url, hdfs_user=hdfs_user).annotate(ret)
    return ret


def get_corpus_name(name, only_class_id=None):
    """
    :rtype: nalaf.structures.data.Dataset
    """
    assert only_class_id == MUT_CLASS_ID, "(corpus name: {}) The class_id to read (only) is always assumed to be `{}`".format(name, MUT_CLASS_ID)

    parts = name.split("_")
    training = test = random = False

    if len(parts) > 1:
        name = parts[0]
        typ = parts[1]
        training = True if typ == "training" else False
        test = True if typ == "test" else False
        random = True if typ == "random" else False
        until_iteration = int(parts[2]) if len(parts) > 2 else None

        if until_iteration:
            assert name == "nala", "Iteration subsets are currently supported only with nala (training or test/indexed, not random/discoveries)"

    if name == "tmVar":
        if not (training or test):
            fn = 'corpus.txt'
        elif training:
            fn = 'train.PubTator.txt'
        elif test:
            fn = 'test.PubTator.txt'

        entirecorpusfile = os.path.join(__corpora_folder, 'tmvar', fn)
        return TmVarReader(entirecorpusfile, MUT_CLASS_ID).read()

    if name == "MF":
        ret = Dataset()

        if not (training or test):
            training = test = True

        if training:
            fn = 'devo_set.txt'
            entirecorpusfile = os.path.join(__corpora_folder, 'mutationfinder', 'cleaned corpus', fn)
            ret.extend_dataset(MutationFinderReader(entirecorpusfile).read())

        if test:
            fn = 'test_set.txt'
            entirecorpusfile = os.path.join(__corpora_folder, 'mutationfinder', 'cleaned corpus', fn)
            ret.extend_dataset(MutationFinderReader(entirecorpusfile).read())

        return ret

    if name == "SETH":
        # this is implementation with everthing into single part
        # ret = SETHReader(os.path.join(__corpora_folder, 'seth', 'corpus.txt')).read()
        # annreader = SETHAnnotationReader(os.path.join(__corpora_folder, 'seth', 'annotations'))
        # annreader.annotate(ret)

        # alternative implementation with abstract and title in separate parts
        ann_folder = os.path.join(__corpora_folder, 'seth', 'annotations')
        pmids = [file[:-4] for file in os.listdir(ann_folder) if file.endswith('.ann')]
        ret = PMIDReader(pmids).read()
        DownloadedSETHAnnotationReader(ann_folder, mut_class_id=MUT_CLASS_ID, gene_class_id=None).annotate(ret)

        return ret

    if name == "LEAP-FS":
        corpus_file = os.path.join(__corpora_folder, 'ProteinResidueFullTextCorpus', 'ProteinResidueFullText.tsv')
        ret = ProteinResidueCorpusPartialReader(corpus_file, mut_class_id=MUT_CLASS_ID, residue_class_id=None).read()

        return ret

    elif name == "IDP4":
        return Iteration.read_IDP4()

    elif name == "nala":
        if training:
            return Iteration.read_nala_training(until_iteration)
        elif test:
            return Iteration.read_nala_test(number_iterations=until_iteration)
        elif random:
            return Iteration.read_nala_random()
        else:
            return Iteration.read_nala()

    elif name == "IDP4+":
        if training:
            return Iteration.read_IDP4Plus_training(until_iteration)
        elif test:
            return Iteration.read_IDP4Plus_test()
        else:
            return Iteration.read_IDP4Plus()

    elif name == "Var":
        folder = os.path.join(__corpora_folder, 'variome', 'data')
        return VerspoorReader(folder, mut_class_id=MUT_CLASS_ID, gene_class_id=None).read()

    elif name == "Var120":
        folder = os.path.join(__corpora_folder, 'variome_120', 'annotations_mutations_explicit')
        return VerspoorReader(folder, mut_class_id=MUT_CLASS_ID, gene_class_id=None).read()

    elif name == "OSIRIS":
        file = os.path.join(__corpora_folder, 'osiris', 'OSIRIScorpusv01.xml')
        return OSIRISReader(file, MUT_CLASS_ID).read()

    elif name in ALL_CORPORA:
        return Dataset()
        # raise NotImplementedError("My bad, not implemented: " + name)

    else:
        raise Exception("Do not recognize given corpus name: " + name)
