# -*- coding: utf-8 -*

import jieba.posseg as pseg
import jieba
import re
import os
from collections import defaultdict
from nltk import pos_tag, word_tokenize, sent_tokenize, ne_chunk
from nltk.tag.stanford import StanfordNERTagger

from crawlTools import *
from namedEntityTools import *
#from loadTools import *

def NER_PO(articleType, articleUrl='', autoCrawlAI=False, articleNumberAI=10, contentMode=[1,1,0], useExpanded=[1, 0, 1], accurateMode=False, dirName='outputs'):
    '''
    input:  articleType: string, 'AIDaily' or other, case insensitive;
            articleUrl: string, default to '';
            autoCrawlAI: boolean, only work when articleType='AI Daily', default to True;
            articleNumberAI: int, only work when articleType='AI Daily' and autoCrawlAI=True, default to 10;
            contentMode: list of int, 1 for use, 0 for ignore. 3 digits stand for: [title, content, description]
            useExpanded: whether or not to use expanded words, 1 for use, 0 for not, 3 digits stand for: [organization, people, undefined]
            accurateMode: whether or not to use StanfordNERTagger, which is more accurate but computationaly more expensive.
            dirName: string, deafult to 'test.txt'
    output: a txt file with organization, people, relations printed
    
    '''
    specialN = ['nr','ns','nt','nz','nl','ng','nrt','nrfg','vn','ENG-ORG','ENG-PEO','CONF']
    lastNameDict = txtToDict("../docs/last name.txt")
    StanfordTagger = StanfordNERTagger('../docs/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz', '../docs/stanford-ner-2014-08-27/stanford-ner.jar')

    titleList = createDict('../docs/titles.txt')


    def helper(title, content, description, contentMode, useExpanded, accurateMode, fileName):
        sentences = splitSentence(title, content, description, contentMode)
        peopleList = []
        orgList = []
        undfList = []
        relationList = []
        engTagDict = defaultdict(int)
        senDict = defaultdict(list)
        nameDict = defaultdict(str)
        for sen in sentences:
            words = generatorToList(pseg.cut(sen))
            i = 0
            SEli = []
            nouns = []
            flags = []
            while i < len(words):
                word, flag = words[i]
                if flag in specialN+['eng']:
                    if flag == 'eng':
                        start, end, expandedWord = expandNoun(i, words, specialN)
                        if expandedWord in engTagDict:
                            tag = engTagDict[expandedWord]
                        else:
                            tag = engTagging(expandedWord, accurateMode, StanfordTagger)
                            engTagDict[expandedWord] = tag
                    else:
                        if word in engTagDict:
                            tag = engTagDict[word]
                        else:
                            tag = tagJudge(word, flag, lastNameDict)
                            engTagDict[word] = tag
                    if useExpanded[tag] and flag != 'eng':
                        start, end, expandedWord = expandNoun(i, words, specialN+['n'])
                    elif flag != 'eng':
                        start, end = i, i+1
                        expandedWord = word
                    nouns.append(expandedWord)
                    flags.append(tag)

                    if expandedWord not in orgList+peopleList+undfList:
                        if tag == 0:
                            ## organization
                            #senDict[sen][expandedWord] = 'O'
                            #nameDict[expandedWord] = 'O'
                            ##
                            orgList.append(expandedWord)
                        elif tag == 1:
                            ## people
                            #senDict[sen][expandedWord] = 'P'
                            #nameDict[expandedWord] = 'P'
                            ##
                            currTitle = [t.decode('utf-8') for t in containKeyWords(sen, titleList)]
                            if currTitle:
                                expandedWord += ''.join(list(set(currTitle)))
                            peopleList.append(expandedWord)
                        else:
                            ## undefined
                            #senDict[sen][expandedWord] = 'U'
                            #nameDict[expandedWord] = 'U'
                            ##
                            undfList.append(expandedWord)

                    SEli.append([start, end])
                    i = end
                else:
                    i += 1


            ans, newFlags, verbs, names = findVerb(SEli, nouns, flags, words)
            if ans and (''.join(ans) not in relationList):
                ####
                senDict[sen] = [ans, verbs, names]
                ####
                relationList.append(''.join(ans))
             

        saveToTxt(title, [orgList, peopleList, undfList, relationList], ['机构'.decode('utf-8'),'人物'.decode('utf-8'),'不确定'.decode('utf-8'),'关系对'.decode('utf-8')], fileName=fileName)
        ##
        #return senDict, nameDict, peopleList, orgList, undfList
        return senDict
        ##


    crawlResults = crawlArticle(articleType, articleUrl, autoCrawlAI, articleNumberAI)
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    if articleType.lower() == 'aidaily' and (autoCrawlAI or not articleUrl):
        titles = crawlResults[0]
        contents = crawlResults[1]
        if not os.path.exists(dirName):
            os.makedirs(dirName)

        for i in range(len(titles)):
            title = titles[i]
            content = contents[i]
            description = ''
            return helper(title, content, description, contentMode, useExpanded, accurateMode, dirName+'/'+'PO_'+title+'.txt')
    else:
        title = crawlResults[0][0]
        content = crawlResults[1][0]
        description = crawlResults[2][0] if crawlResults[2] else ''
        return helper(title, content, description, contentMode, useExpanded, accurateMode, dirName+'/'+'PO_'+title+'.txt')
    

if __name__ == "__main__":
    # 长文章，给定url提取
    NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-10-25-8')
    #NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-08-16')
    #NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-08-8')
    #NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-20-5')
    

    
    # AI Daily 类型文章，给定url提取
    #NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies/2f2d4ee1-9486-4aa5-84fa-fd76f2ae7239', dirName='outputs/AIDailyByURL tests')
    #NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies/bfcb0416-1695-4a08-95b3-b00208f7271d', dirName='outputs/AIDailyByURL tests')
    #NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies?id=62a92b37-6f86-4798-ae65-3d9fad8dabaf', dirName='outputs/AIDailyByURL tests')

    # AI Daily类型文章，自动提取
    #NER_PO('AIDaily', autoCrawlAI=True, articleNumberAI=5, dirName='outputs/AIDailyAuto tests')
