# -*- coding: UTF-8 -*
import os

import CRFPP

import config
from logger_manager import seg_api_logger as logger
from bin.term_tuple import CrfRegResult, NameTerm, WordTerm
from util.tool import get_closest_file


class RecCom:
    def __init__(self, modelfile=None, nbest=None,):

        if not nbest:
            nbest = 1
        if not modelfile:
            assert False

        self.tagger = CRFPP.Tagger('-n '+str(nbest)+' -m ' + modelfile)
        self.tagger.clear()
        self.begin = "#SENT_BEG#\tbegin"
        self.end = "#SENT_BEG#\tend"
        self.terms = []

    def _add(self, atts):
        result = str(atts)
        self.tagger.add(result)

    def addterms(self, termlist):
        self._add(self.begin)
        for term in termlist:
            self._add(term)
        self._add(self.end)

    def clear(self):
        self.terms.clear()
        self.tagger.clear()

    def parse(self):
        if not self.tagger.parse():
            return self.terms
        for n in range(self.tagger.nbest()):
            if not self.tagger.next():
                break
            termlist = []
            for i in range(self.tagger.size()):
                term = CrfRegResult(self.tagger.x(i, 0))
                term.set_wheater(self.tagger.yname(self.tagger.y(i)))
                termlist.append(term)
            self.terms.append(termlist)
        return self.terms


def reg_result_classify(company_name, rich_termlist):
    result = NameTerm(company_name)
    s_offset = 0
    e_offset = 0
    word_str = ''
    word_type = 'OUT'
    for richterm in rich_termlist:
        if richterm.char == '#':
            continue
        before_type = word_type
        mark = richterm.wheater
        if 'R' in mark:
            word_type = 'R'
        elif 'I' in mark:
            word_type = 'I'
        elif 'U' in mark:
            word_type = 'U'
        elif 'O' in mark:
            word_type = 'O'

        if '_S' in mark:
            if word_str.strip():
                one = WordTerm(word_str, s_offset, e_offset-1)
                one.set_type(before_type)
                result.add_word_term(one)
                s_offset = e_offset
            one = WordTerm(richterm.char, s_offset, e_offset)
            one.set_type(word_type)
            result.add_word_term(one)
            s_offset += 1
            e_offset += 1
            word_str = ''
        elif '_B' in mark:
            if word_str.strip():
                one = WordTerm(word_str, s_offset, e_offset-1)
                one.set_type(before_type)
                result.add_word_term(one)
                s_offset = e_offset
            word_str = ''
            word_str = ''.join([word_str, richterm.char])
            e_offset += 1
        elif '_M' in mark:
            word_str = ''.join([word_str, richterm.char])
            e_offset += 1
        elif '_E' in mark:
            word_str = ''.join([word_str, richterm.char])
            one = WordTerm(word_str, s_offset, e_offset)
            one.set_type(word_type)
            result.add_word_term(one)
            word_str = ''
            e_offset += 1
            s_offset = e_offset
    if word_str.strip():
        one = WordTerm(word_str, s_offset, e_offset)
        one.set_type(word_type)
        result.add_word_term(one)
    return result


def get_model_abbr(company_name, g=None):
    fullname = list(company_name)
    if g and not str(g) == 'Namespace()':
        rm_instance = RecCom(g.load_model_path)
    else:
        if not os.path.exists(config.CLASSSIFY_MODEL_FILE):
            config.CLASSSIFY_MODEL_FILE = get_closest_file(config.CLASSSIFY_MODEL_PATH, '_crf_abbr_classify_model')

        rm_instance = RecCom(config.CLASSSIFY_MODEL_FILE)
        rm_instance.addterms(fullname)

    rich_termlist = rm_instance.parse()
    result = reg_result_classify(company_name, rich_termlist[0])
    result.merge_wterm_include_type(None)
    logger.info(result.set_api_json())
    rm_instance.clear()
    return result


if __name__ == '__main__':
    print(get_model_abbr('中国电建集团成都勘测设计研究院有限公司').set_api_json())
