import pkg_resources
import csv
import re
from nalaf.structures.data import Entity

from nala.preprocessing.definers import ExclusiveNLDefiner
from nala.utils import MUT_CLASS_ID


class PostProcessing:

    def __init__(self, keep_silent=True, keep_genetic_markers=True, keep_unnumbered=True, keep_rs_ids=True):

        amino_acids = [
            'alanine', 'ala', 'arginine', 'arg', 'asparagine', 'asn', 'aspartic acid', 'aspartate', 'asp',
            'cysteine', 'cys', 'glutamine', 'gln', 'glutamic acid', 'glutamate', 'glu', 'glycine', 'gly',
            'histidine', 'his', 'isoleucine', 'ile', 'leucine', 'leu', 'lysine', 'lys', 'methionine', 'met',
            'phenylalanine', 'phe', 'proline', 'pro', 'serine', 'ser', 'threonine', 'thr', 'tryptophan', 'trp',
            'tyrosine', 'tyr', 'valine', 'val', 'aspartic acid', 'asparagine', 'asx', 'glutamine', 'glutamic acid',
            'glx']

        nucleotides = ['adenine', 'guanine', 'thymine', 'cytosine', 'uracil']

        keywords = ['substit\w*', 'lead\w*', 'exchang\w*', 'chang\w*', 'mutant\w*', 'mutate\w*', 'devia\w*', 'modif\w*',
                    'alter\w*', 'switch\w*', 'variat\w*', 'instead\w*', 'replac\w*', 'in place', 'convert\w*',
                    'becom\w*']

        # AA = '|'.join(amino_acids)
        AA_NN = '|'.join(amino_acids + nucleotides)
        AA_LL = '|'.join(amino_acids + list('CISQMNPKDTFAGHLRWVEYX'))
        KK = '|'.join(keywords)

        genetic_marker_regex = re.compile(r'\bD\d+([A-Z]\d+)?S\d{2,}\b')
        rs_id_regex = re.compile(r'\b\[?rs\]? *\d{3,}(,\d+)*\b')
        ss_id_regex = re.compile(r'\b\[?ss\]? *\d{3,}(,\d+)*\b')

        self.patterns = [
            re.compile('({SS})[- ]*[1-9][0-9]* +(in|to|into|for|of|by|with|at) +({SS})( *(,|,?or|,?and) +({SS}))*'
                       .format(SS=AA_NN), re.IGNORECASE),
            re.compile('({SS}) +(in|to|into|for|of|by|with|at) +({SS})[- ]*[1-9][0-9]*'
                       '( *(,|,?or|,?and) +({SS})[- ]*[1-9][0-9]*)*'
                       .format(SS=AA_NN), re.IGNORECASE),
            re.compile('({SS})(( (({KK})) (in|to|into|for|of|by|with|at) (a|an|the|) '
                       '*({SS})[1-9]\d*( *(,|or|and|, and|, or) ({SS})[1-9]\d*)*)'
                       '|([- ]*[1-9]\d*( +((has|have|had) +been|is|are|was|were|) '
                       '+(({KK})))? +(in|to|into|for|of|by|with|at) +({SS})( *(,|or|and|, and|, or) +({SS}))*))'
                       .format(SS=AA_NN, KK=KK), re.IGNORECASE),

            re.compile(r'\bp\. *({SS}) *[-+]*\d+ *({SS})\b'.format(SS=AA_NN), re.IGNORECASE),
            re.compile(r'\b({SS})[-to ]*[-+]*\d+[-to ]*({SS})\b'.format(SS=AA_NN), re.IGNORECASE),

            re.compile(r'\b[CISQMNPKDTFAGHLRWVEYX](/|-|-*>|→|-to-)[CISQMNPKDTFAGHLRWVEYX] *[-+]*\d+\b'),
            re.compile(r'((?<!\w)[-+]*\d+:? *?)??[CISQMNPKDTFAGHLRWVEYX] *(/|-|-*>|→|-*to-*) *[CISQMNPKDTFAGHLRWVEYX]\b'),

            re.compile(r'\b[CISQMNPKDTFAGHLRWVEYX]{3,}/-(?<!\w)'),

            re.compile(r'\b[CISQMNPKDTFAGHLRWVEYX] *\d{2,} *[CISQMNPKDTFAGHLRWVEYX]( *(/) *[CISQMNPKDTFAGHLRWVEYX])*\b'),

            genetic_marker_regex,
            rs_id_regex,
            ss_id_regex,

            re.compile(r'\b(\d+-)?\d*[D|d]elta(\d{2,}|[CISQMNPKDTFAGHLRWVEYX])\b'),

            re.compile(r'\b(c\. *)?[ATCG] *([-+]|\d)\d+ *[ATCG]\b'),
            re.compile(r'\b(c\.|E(X|x)\d+) *([-+]|\d)\d+[ATCG] *> *[ATCG]\b'),
            re.compile(r'\b[ATCG][-+]*\d+[ATCG]/[ATCG]\b'),

            re.compile(r'(?<!\w)[-+]?\d+ *\d* *(b|bp|N|ntb|p|BP|B) *(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup)\b'),
            re.compile(r'(?<!\w)[-+]*\d+ *(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup)[0-9CISQMNPKDTFAGHLRWVEYX]+\b'),
            re.compile(r'\b[CISQMNPKDTFAGHLRWVEYX]+ *[-+]*\d+ *(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup)\b'),
            re.compile(r'\b(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup) *(\d+(b|bp|N|ntb|p|BP|B)|[ATCG]{1,})\b'),
            re.compile(r'(?<!\w)[-+]*\d+ *(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup)[CISQMNPKDTFAGHLRWVEYX]+\b'),
            re.compile(r'\b[CISQMNPKDTFAGHLRWVEYX]+ *[-+]*\d+ *(INS|DEL|INDEL|DELINS|DUP|ins|del|indel|delins|dup)\b')
        ]

        self.negative_patterns = [
            # single AAs
            re.compile(r'^({SS}) *\d+$'.format(SS=AA_NN), re.IGNORECASE),
            re.compile(r'^[CISQMNPKDTFAGHLRWVEYX]+ *\d+$'),
            re.compile(r'^({SS})([-/>]({SS}))*$'.format(SS=AA_LL), re.IGNORECASE),
            # just numbers
            re.compile(r'^[-+]?\d+([-+/ ]+\d+)*( *(b|bp|N|ntb|p|BP|B))?$')
        ]

        if not keep_genetic_markers:
            self.negative_patterns.append(genetic_marker_regex)

        if not keep_rs_ids:
            self.negative_patterns.append(rs_id_regex)
            self.negative_patterns.append(ss_id_regex)

        self.keep_unnumbered = keep_unnumbered

        self.at_least_one_letter_n_number_letter_n_number = re.compile('(?=.*[A-Za-z])(?=.*[0-9])[A-Za-z0-9]+')
        self.keep_silent = keep_silent
        self.definer = ExclusiveNLDefiner()

    def process(self, dataset, class_id=MUT_CLASS_ID):
        for doc_id, doc in dataset.documents.items():
            for part_id, part in doc.parts.items():
                self.__fix_issues(part)
                for regex in self.patterns:
                    for match in regex.finditer(part.text):
                        start = match.start()
                        end = match.end()
                        matched_text = part.text[start:end]
                        ann = Entity(class_id, start, matched_text)

                        Entity.equality_operator = 'exact_or_overlapping'
                        if ann not in part.predicted_annotations:
                            part.predicted_annotations.append(Entity(class_id, start, matched_text))
                        Entity.equality_operator = 'overlapping'
                        if ann in part.predicted_annotations:
                            for index, ann_b in enumerate(part.predicted_annotations):
                                if ann == ann_b and len(matched_text) > len(ann_b.text):
                                    part.predicted_annotations[index] = ann

                to_delete = [index for index, ann in enumerate(part.predicted_annotations)
                             if any(r.search(ann.text) for r in self.negative_patterns)
                             or (not self.keep_silent and self.__is_silent(ann))
                             or (not self.keep_unnumbered and not self._is_numbered(ann))]

                part.predicted_annotations = [ann for index, ann in enumerate(part.predicted_annotations)
                                              if index not in to_delete]

        # sanity check, make sure annotations match their offset
        for part in dataset.parts():
            for ann in part.predicted_annotations:
                assert ann.text == part.text[ann.offset:ann.offset + len(ann.text)]
                while ann.text[0] == ' ':
                    ann.offset += 1
                    ann.text = ann.text[1:]
                while ann.text[-1] == ' ':
                    ann.text = ann.text[:-1]
                # assert ann.text == ann.text.strip(), ("'" + ann.text + "'")

    def __is_silent(self, ann):
        split = re.split('[^A-Za-z]+', ann.text)
        return len(split) == 2 and split[0] == split[1]

    def _is_numbered(self, ann):
        return any(c.isdigit() for c in ann.text) or self.definer.define_string(ann.text) == 1

    def __fix_issues(self, part):
        """
        :type part: nalaf.structures.data.Part
        """
        to_be_removed = []
        for index, ann in enumerate(part.predicted_annotations):
            start = ann.offset
            end = ann.offset + len(ann.text)

            # split multiple mentions
            split = re.split(r' *(?:\band\b|/|\\|,|;|\bor\b) *', ann.text)
            if len(split) > 1:
                # for each split part calculate the offsets and the constraints
                offset = 0
                split_info = []
                for text in split:
                    split_info.append((text, self.definer.define_string(text), ann.text.find(text, offset),
                                       self.at_least_one_letter_n_number_letter_n_number.search(text)))
                    offset += len(text)

                split_parts = [split_part for split_part in split_info if split_part[0] != '']
                lens = [len(split_part[0]) for split_part in split_parts]
                patterns = [re.sub('\W+', '', re.sub('[0-9]', '0', re.sub('[a-zA-Z]', 'a', parts[0]))) for parts in split_parts]

                # if all the non empty parts are from class ST (0) and also contain at least one number and one letter
                # or if the lengths of the splitted parts are the same or follow the same pattern
                if all(split_part[1] == 0 and split_part[3] for split_part in split_parts) or max(lens) == min(lens) or len(set(patterns)) == 1:
                    to_be_removed.append(index)

                    # add them to
                    for split_text, split_class, split_offset, aonanl in split_info:
                        if split_text != '':
                            part.predicted_annotations.append(
                                Entity(ann.class_id, ann.offset + split_offset, split_text))

            # fix boundary, 1858C>T --> +1858C>T
            if re.search('^[0-9]', ann.text) and re.search('([\-\+])', part.text[start - 1]):
                ann.offset -= 1
                ann.text = part.text[start - 1] + ann.text
                start -= 1

            # fix boundary delete (
            if ann.text[0] == '(' and ')' not in ann.text:
                ann.offset += 1
                ann.text = ann.text[1:]
                start += 1

            # fix boundary delete )
            if ann.text[-1] == ')' and '(' not in ann.text:
                ann.text = ann.text[:-1]

            # fix boundary add missing (
            if part.text[start - 1] == '(' and ')' in ann.text:
                ann.offset -= 1
                ann.text = '(' + ann.text
                start -= 1

            # fix boundary add missing )
            try:
                if part.text[end] == ')' and '(' in ann.text:
                    ann.text += ')'
            except IndexError:
                pass

            # fix boundary add missing number after fsX
            try:
                found_missing_fsx = False
                if part.text[end:end + 2] == 'fs':
                    ann.text += 'fs'
                    end += 2
                    found_missing_fsx = True
                if ann.text.endswith('fs') and part.text[end] == 'X':
                    ann.text += 'X'
                    end += 1
                    found_missing_fsx = True
                if found_missing_fsx:
                    while part.text[end].isnumeric():
                        ann.text += part.text[end]
                        end += 1
            except IndexError:
                pass

            # fix boundary add missing c. or p. before ann
            try:
                if ann.text.startswith('.'):
                    if part.text[start - 1] in ('c', 'p'):
                        ann.offset -= 1
                        ann.text = part.text[start - 1] + ann.text
                        start -= 1
                elif part.text[start - 2:start] in ('c.', 'p.', 'rt'):
                    ann.offset -= 2
                    ann.text = part.text[start - 2:start] + ann.text
                    start -= 2
            except IndexError:
                pass

            # fix boundary add missing \d+ at the beginning
            if ann.text[0] == '-' or part.text[start-1] == '-':
                tmp = start
                while tmp - 1 > 0 and (part.text[tmp-1].isnumeric() or part.text[tmp-1] == '-'):
                    tmp -= 1
                if part.text[tmp - 1] == ' ':
                    ann.offset = tmp
                    ann.text = part.text[ann.offset:start] + ann.text
                    start = tmp

            isword = re.compile(r'\w')

            # The word must end in space to the left
            # not matched: 'and+2740 A>G'
            if isword.search(ann.text[0]) and \
                (not (ann.offset >= 3 and part.text[ann.offset - 3: ann.offset] == "and"
                or (ann.offset >= 2 and part.text[ann.offset - 2: ann.offset] == "or"))):

                while ann.offset > 0 and isword.search(part.text[ann.offset - 1]):
                    ann.text = part.text[ann.offset - 1] + ann.text
                    ann.offset -= 1

            veryend = len(part.text)
            end = ann.offset + len(ann.text)

            # The word must end in space to the right
            while end < veryend and isword.search(part.text[end]):
                ann.text = ann.text + part.text[end]
                end += 1

            # Remove parenthesis if within parenthesis but no parentesis either in between
            if ann.text[0] in ['('] and ann.text[-1] in [')'] and (ann.text.count('(') < 2 and ann.text.count(')') < 2):
                ann.offset += 1
                ann.text = ann.text[1:-1]

            # Follow the rule of abbreviations + first gene mutation (then protein mutation)
            if ((ann.text[-1] == ')' or (end < veryend and part.text[end] == ")")) and ann.text[:-1].count('(') == 1):
                # Requirement 1: must be space to the left of (, not to match things like in Arg407(AGG) or IVS3(+1)
                p = re.compile("\\s+\\(")
                split = p.split(ann.text)
                if len(split) == 2:

                    # Requirement 2: both parths must contain a number (== position, they can stand alone)
                    def req2():
                        return any(c.isdigit() for c in split[0]) and any(c.isdigit() for c in split[1])

                    # Other Reqs on left part
                    def req3():
                        return any(c.isalpha() for c in split[0].replace('and', '').replace('or', ''))

                    # Other Reqs on right part
                    def req4():
                        return any(c.isalpha() for c in split[1].replace('and', '').replace('or', ''))

                    if req2() and len(split[0]) > 2 and req3() and req4():
                        # Neg.: Arg407(AGG) - single amino acid substitution (Phe for Val) - nonsense mutation (286T)
                        # Neg.: deletion (229bp) -  nonsense mutation (glycine 568 to stop)
                        # Neg.: one insertion mutation (698insC) - AChR epsilon (CHRNE E376K)
                        # Neg. (other reqs): M1 (Val213) - 207 and 208 (207-HA)
                        # Neg. (other reqs): located 14 amino acids toward the amino-terminal end from the (682)
                        #
                        # Pos.: serine to arginine at the codon 113 (p. S113R)
                        # Pos.: mutagenesis of the initial ATG codon to ACG (Met 1 to Thr) - H2A at position 105 (Q105)
                        # Pos.: Trp replacing Gln in position 156 (A*2406) - A-1144-to-C transversion (K382Q)
                        # Pos: deletion of 123 bases (41 codons) - exon 12 (R432T)

                        ann1text = split[0]
                        to_be_removed.append(index)
                        part.predicted_annotations.append(Entity(ann.class_id, ann.offset, ann1text))
                        ann2text = split[1] if ann.text[-1] != ')' else split[1][:-1]
                        # last part is number of spaces + (
                        ann2offset = ann.offset + len(ann1text) + (len(ann.text) - sum(len(x) for x in split))
                        part.predicted_annotations.append(Entity(ann.class_id, ann2offset, ann2text))

        part.predicted_annotations = [ann for index, ann in enumerate(part.predicted_annotations)
                                      if index not in to_be_removed]


def construct_regex_patterns_from_predictions(dataset):
    """
    :type dataset: nalaf.structures.data.Dataset
    """
    regex_patterns = []
    for ann in dataset.predicted_annotations():
        item = ann.text
        # escape special regex characters
        item = item.replace('.', '\.').replace('+', '\+').replace(')', '\)').replace('(', '\(').replace('*', '\*')

        # numbers pattern
        item = re.sub('[0-9]+', '[0-9]+', item)

        # take care of special tokens
        item = re.sub('(IVS|EX)', '@@@@', item)
        item = re.sub('(rs|ss)', '@@@', item)

        # letters pattern
        item = re.sub('[a-z]', '[a-z]', item)
        item = re.sub('[A-Z]', '[A-Z]', item)

        # revert back special tokens
        item = re.sub('@@@@', '(IVS|EX)', item)
        item = re.sub('@@@', '(rs|ss)', item)

        # append space before and after the constructed pattern
        regex_patterns.append(re.compile(r'( |rt)({}) '.format(item)))

    base_regex = r'\b(rt)?({})\b'
    # include already prepared regex patterns
    # modified by appending space before and after the original pattern
    with open(pkg_resources.resource_filename('nala.data', 'RegEx.NL')) as file:
        for regex in csv.reader(file, delimiter='\t'):
            if regex[0].startswith('(?-xism:'):
                try:
                    regex_patterns.append(re.compile(base_regex.format(regex[0].replace('(?-xism:', '')),
                                                     re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE))
                except Exception as e:
                    if e.args[0] == 'sorry, but this version only supports 100 named groups':
                        # if the exception is due to too many named groups
                        # make the groups unnamed since we don't need them to be named in the frist place
                        fixed = regex[0].replace('(?-xism:', '')
                        fixed = re.sub('\((?!\?:)', '(?:', fixed)
                        regex_patterns.append(re.compile(base_regex.format(fixed)))


            else:
                regex_patterns.append(re.compile(base_regex.format(regex[0])))

    # add our own custom regex
    regex_patterns.append(re.compile(base_regex.format('[ATCG][0-9]+[ATCG]/[ATCG]')))

    return regex_patterns
