# -*- coding: utf-8 -*
import jieba
import re
def loadDicts(keyWords):
    for word in keyWords:
        jieba.add_word(word.strip(), tag='FNC')
    print ('Customized dicts has been built succesfully.')
#loadDicts(["../docs/combined-conference.txt"])
