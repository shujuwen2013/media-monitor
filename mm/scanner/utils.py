# -*- coding: utf-8 -*-

import jieba.posseg as pseg
import jieba


# tokenization without punctuations 
def tokenize_text(text):
    # adjust dict
    jieba.suggest_freq(('看', '电视'), True)
    # cut words
    nv_words = []
    for word, flag in pseg.cut(text):
        # http://blog.csdn.net/li_31415/article/details/48660073
        if flag[0] not in 'x':
        #print('%s %s' % (word, flag))
            nv_words.append(word.lower())
    return nv_words