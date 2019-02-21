# -*- coding: utf-8 -*
import jieba
import re
def loadDicts(fileList=[]):
    for f in fileList:
        # jieba.load_userdict(dict)

        file = open(f, 'r') 
        lines = file.readlines()

        for line in lines:
            '''
            phrase = line.decode('utf-8')
            wordList = [phrase]
            replaced = re.sub('[-,\(\)（）]'.decode('utf-8'), '-', phrase)
            replaced = re.sub('[ ]+'.decode('utf-8'), ' ', replaced)
            wordList.append(replaced)
            wordList += replaced.split('-')
            for word in wordList:
                if 'organization' in f and word:
                    if (u'\u4e00' <= word[0] and word[0] <= u'\u9fff'):
                        jieba.add_word(word.strip(), tag='nt')
                    elif len(word) > 5:
                        jieba.add_word(word.strip(), tag='ENG-ORG')
                elif 'people' in f and word:
                    if (u'\u4e00' <= word[0] and word[0] <= u'\u9fff'):
                        jieba.add_word(word.strip(), tag='nr')
                    else:
                        jieba.add_word(word.strip(), tag='ENG-PEO')
                elif 'conf' in f and word:
                    if (u'\u4e00' <= word[0] and word[0] <= u'\u9fff'):
                        jieba.add_word(word.strip(), tag='CONF')
                    else:
                        jieba.add_word(word.strip(), tag='CONF')
            '''
            conf = line.decode('utf-8')
            jieba.add_word(conf.strip(), tag='CONF')

loadDicts(["../docs/combined-conference.txt"])
print 'Customized dicts has been built succesfully.'