import argparse

from nala.preprocessing.definers import ExclusiveNLDefiner
from nala.utils.corpora import get_corpus, ALL_CORPORA
from nala.utils import MUT_CLASS_ID
from nalaf.structures.dataset_pipelines import PrepareDatasetPipeline
from nalaf.structures.data import Dataset
# from collections import Counter

parser = argparse.ArgumentParser(description='Print corpora stats')

parser.add_argument('corpora', default='*', metavar='corpus', nargs='+',
                    help='Name of the corpus to read and print stats for')
parser.add_argument('--listanns', default="",
                    help='Print mutation comma-separated subclasses. Examples: 1 or 1,2 or * for all')
parser.add_argument('--counttokens', help='Count the tokens. Note, this is considerably slower', action='store_true')

args = parser.parse_args()

if args.corpora[0] == "*" or args.corpora[0] == 'all':
    args.corpora = ALL_CORPORA

if args.listanns == '*' or args.listanns == 'all':
    args.listanns = '0,1,2'
args.listanns = set(int(c) for c in args.listanns.split(",") if c)

# ------------------------------------------------------------------------------

nldefiner = ExclusiveNLDefiner()

pipeline = PrepareDatasetPipeline(feature_generators=[])

ST = 0  # Standard
NL = 1  # Natural Language
SST = 2  # Semi-Standard -- also often denoted before as 'SS'

MARKER = [
    '        ',
    '@@@@@@@@',
    '********'
]

PROB = "{0:.3f}"  # FORMAT

# ------------------------------------------------------------------------------

def get_corpus_type(name):
    if name == "MF":
        return (name, None)
    elif name.endswith("A"):
        return (name[:-1], "A")
    elif name.endswith("F"):
        return (name[:-1], "F")
    else:
        return (name, None)

def is_part_type(part, typ):
    return not typ or (typ == "A" and part.is_abstract) or (typ == "F" and not part.is_abstract)

def is_abstract_only(document):
    return all(part.is_abstract for part in document)

def is_full_text(document):
    return any(not part.is_abstract for part in document)

def corpus_annotations(corpus, typ):
    for docid, document in corpus.documents.items():
        for part in document:
            if is_part_type(part, typ):
                for annotation in part.annotations:
                    yield annotation

def doc_annotations(document, typ):
    for partid, part in document.parts.items():
        if is_part_type(part, typ):
            for annotation in part.annotations:
                yield partid, annotation

def get_num_tokens(corpus, typ):
    if (args.counttokens):
        pipeline.execute(corpus)  # obtain tokens

        ret = 0
        for part in corpus.parts():
            if is_part_type(part, typ):
                for sentence in part.sentences:
                    ret += len(sentence)

        return ret
    else:
        return -1

def filter_only_full_text(corpus):
    newcorpus = Dataset()
    for docid, document in corpus.documents.items():
        if is_full_text(document):
            newcorpus.documents[docid] = document

    return newcorpus


# WordsCounter = Counter()

def get_stats(name, corpus, typ):
    nldefiner.define(corpus)  # classify subclasses

    corpus = filter_only_full_text(corpus) if typ == "F" else corpus
    counts_total = 0
    counts_subs = [0, 0, 0]
    uniq_total = set()
    uniq_subs = [set(), set(), set()]

    num_docs_with_anns = 0
    num_docs_with_NL = 0
    num_docs_with_NL_untraslated = 0
    num_NLs_untranslated = 0

    for docid, document in corpus.documents.items():
        doc_has_anns = False
        doc_has_NL = False
        docs_num_NL = 0

        for partid, ann in doc_annotations(document, typ):
            if ann.class_id == MUT_CLASS_ID:
                doc_has_anns = True
                counts_total += 1
                counts_subs[ann.subclass] += 1
                e_uid = ann.text  # We want to compare by text. Irrelevant: ann.gen_corpus_uniq_id(docid, partid)
                uniq_total.add(e_uid)
                uniq_subs[ann.subclass].add(e_uid)

                if ann.subclass != ST:  # This considers Alex's manual definition, i.e. NL = NL + SST
                    doc_has_NL = True
                    docs_num_NL += 1

                if ann.subclass in args.listanns:
                    print('\t' + '#' + str(counts_total) + ' (' + str(len(uniq_total)) + ')  ' + str(ann.subclass) + ' ' + MARKER[ann.subclass] + ' : ' + ann.text)

        if doc_has_anns:
            num_docs_with_anns += 1

        if doc_has_NL:
            num_docs_with_NL += 1

            num_relations = len(list(document.relations()))
            # This is a simplification and pesimistic estimation. The relations could be between NLs or involve a lower number of NLs
            untranslated = num_relations == 0

            if untranslated:
                num_docs_with_NL_untraslated += 1
                num_NLs_untranslated += docs_num_NL

    num_docs = len(corpus.documents)
    num_empty_docs = num_docs - num_docs_with_anns
    num_tokens = get_num_tokens(corpus, typ)
    percents = list(map(lambda x: (PROB.format(x / counts_total) if x > 0 else "0"), counts_subs))
    u_percents = list(map(lambda x: (PROB.format(len(x) / len(uniq_total)) if len(x) > 0 else "0"), uniq_subs))
    per_docs_with_NL_untraslated = PROB.format((num_docs_with_NL_untraslated / num_docs) if num_docs != 0 else 0)
    per_NLs_untraslated = PROB.format((num_NLs_untranslated / counts_total) if counts_total != 0 else 0)

    # if (args.listall):
    #     print('\t'.join(header))

    # The limit of 7 for the corpus name is the size that fits into a tab column, so that it looks good on print
    return [
        name[:7],
        num_docs,
        num_empty_docs,
        num_tokens,
        counts_total, counts_subs[ST], percents[ST], counts_subs[NL], percents[NL], counts_subs[SST], percents[SST], (counts_subs[NL] + counts_subs[SST]), PROB.format(0 if (counts_total == 0) else (1 - float(percents[ST]))),
        len(uniq_total), len(uniq_subs[ST]), u_percents[ST], len(uniq_subs[NL]), u_percents[NL], len(uniq_subs[SST]), u_percents[SST], (len(uniq_subs[NL]) + len(uniq_subs[SST])), PROB.format(0 if (len(uniq_total) == 0) else (1 - float(u_percents[ST]))),
        per_docs_with_NL_untraslated, per_NLs_untraslated
    ]

# ------------------------------------------------------------------------------

# The following measures currently only apply to the corpus nala_random, which has the appropriate relation annotations
#
# %d_u_NL == percentage of documents that have at least one untranslated NL mention
# %m_u_NL == percentage of mentions that are NL and are untranslated to ST
header = [
    "#Corpus",
    "#docs",
    "#e_docs",  # number of _empty_ docs (i.e. without annotations)
    "#tokens",
    "#ann", "#ST", "%ST", "#NL", "%NL", "#SST", "%SST", "#NL+SST", "%NL+SST",
    "u#ann", "u#ST", "u%ST", "u#NL", "u%NL", "u#SST", "u%SST", "u#NL+SS", "u%NL+SS", #here called SS (not SST) for lack of column width space for pretty alignment
    "%d_u_NL", "%m_u_NL"
]

print('\t'.join(header))

for corpus_name in args.corpora:
    realname, typ = get_corpus_type(corpus_name)
    corpus = get_corpus(realname, only_class_id=MUT_CLASS_ID)
    columns = get_stats(corpus_name, corpus, typ)
    if args.listanns:
        print('\t'.join(header))
    print(*columns, sep='\t')

# for count in WordsCounter.most_common()[:-len(WordsCounter)-1:-1]:
#     print(count)
