# -*- coding: utf-8 -*
from __future__ import print_function, unicode_literals
import pyltp
from pyltp import SentenceSplitter
import re
import os
import sys
from collections import defaultdict
from nltk import pos_tag, word_tokenize, sent_tokenize, ne_chunk
from nltk.tag.stanford import StanfordNERTagger
import json
import requests
from bosonnlp import BosonNLP

from crawlTools import *
from namedEntityTools import *
from loadTools import *
from zh_NER_TF.main import *


from platform import python_version
print(python_version())


# from loadTools import *
def NER_PO(articleType, articleUrl='', autoCrawlAI=False, articleNumberAI=10, contentMode=[1, 1, 0],
           useExpanded=[1, 0, 1], accurateMode=False, dirName='outputs'):
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
    investKeyWords = ['融资', '领投', '跟投', '收购', '合并', '投资', '创投', '获投', '注资', '并购', '参投', '出资', '斥资', '筹资', '筹集', '入股', '增持']
    cooporationKeyWords = ['合作', '结盟', '联合', '对接', '携手', '提供商', '供应商', '联盟', '联手', '牵手', '共建']
    specialN = ['nr', 'ns', 'nt', 'nz', 'nl', 'ng', 'nrt', 'nrfg', 'vn']
    engSpecialN = ['nx','w','wd']
    tagInterpret = ['ORG', 'PEO', 'O']
    lastNameDict = txtToDict("docs/last name.txt")
    StanfordTagger = StanfordNERTagger('docs/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz','docs/stanford-ner-2014-08-27/stanford-ner.jar')
    #nlp = BosonNLP('jj-zE93I.33208.2PLQn2ZwoOOs')
    nlp = BosonNLP('Cpcr3Wym.33210.xQpBxPaHIXmi')

    def helper(title, content, description, contentMode, useExpanded, accurateMode, fileName):
        #sentences = splitSentence(title, content, description, contentMode)
        sentences = list(SentenceSplitter.split(title+content))
        peopleList = []
        orgList = []
        relationDict = defaultdict(list)
        financialDict = defaultdict(list)
        titleDict = defaultdict(list)
        results = nlp.ner(sentences)

        for result in results:
            sen = ''.join(result['word'])
            entities = result['entity']
            bosonWords = []
            for i in range(len(result['word'])):
                bosonWords.append([result['word'][i], result['tag'][i]])

            currRoundList = getRound(sen)
            currRoundString = ', 轮次: ' + ''.join(currRoundList) if ''.join(currRoundList).strip() else ''

            words = []
            start = 0
            for entity in entities:
                words += bosonWords[start:entity[0]]
                if entity[2] in ['org_name','company_name']:
                    words.append([''.join(result['word'][entity[0]:entity[1]]), 'ORG'])
                    if ''.join(result['word'][entity[0]:entity[1]]) not in orgList:
                        orgList.append(''.join(result['word'][entity[0]:entity[1]]))
                elif entity[2] == 'person_name':
                    words.append([''.join(result['word'][entity[0]:entity[1]]), 'PEO'])
                    if ''.join(result['word'][entity[0]:entity[1]]) not in peopleList:
                        peopleList.append(''.join(result['word'][entity[0]:entity[1]]))
                elif entity[2] == 'time':
                    words.append([''.join(result['word'][entity[0]:entity[1]]), 'time'])
                elif entity[2] == 'job_title':
                    words.append([''.join(result['word'][entity[0]:entity[1]]), 'TTL'])
                start = entity[1]
            words += bosonWords[start:]


            # merging and tagging eng words
            i = 0
            while i < len(words):
                word, tag = words[i]
                if tag == 'nx' and (word not in peopleList+orgList):
                    start, end, expandedWord = expandNoun(i, words, engSpecialN)
                    words[i][0] = expandedWord
                    if expandedWord in ''.join(currRoundString):
                        i += 1
                        continue
                    words[i][1] = tagInterpret[engTagging(expandedWord, accurateMode, StanfordTagger)]
                    if words[i][1] == 'PEO':
                        peopleList.append(expandedWord)
                        titleDict[expandedWord.strip()] = []
                    if words[i][1] == 'ORG':
                        orgList.append(expandedWord)
                    i = end
                elif word in investKeyWords+cooporationKeyWords:
                    words[i][1] = 'FNC'
                    i += 1
                else:
                    i += 1

            currPEOList = [[(i, i+1), words[i][0]] for i in range(len(words)) if words[i][1] == 'PEO']
            currTTLList = [[(i, i+1), words[i][0]] for i in range(len(words)) if words[i][1] == 'TTL']
            currORGList = [[(i, i+1), words[i][0]] for i in range(len(words)) if words[i][1] == 'ORG']

            if (not currPEOList) and (not currORGList):
                continue


            currMoneyList = list(set([num for num in findNumber(words) if containKeyWords(num, ['亿', '元', '万'])]))
            currMoneyString = ', 金额: ' + ''.join(currMoneyList) if ''.join(currMoneyList).strip() else ''
            currTimeList = list(set([num[0] for num in words if num[1] == 'time']))
            currTimeString = ', 时间: ' + ''.join(currTimeList) if ''.join(currTimeList).strip() else ''



            # 匹配职位信息
            for _, p in currPEOList:
                titleDict[p.strip()] = []
            titleDict = pairTitle(currPEOList, currTTLList, currORGList, words, titleDict, currTimeString)


            # 找金融动作
            #findFinancialRelation(verbs, sen, currORGList
            financialWords = [k for k in words if k[1] in ['ORG','FNC','w','wj','ww','wt','wd','wf','wn','wm','ws','wp']]
            findFinancialRelation(financialWords, financialDict, currRoundString, currMoneyString, currTimeString)
            print('sen', sen)
            print('HERE', findFinancialRelation)

            # 找动词
            i = 0
            prevNER = ''
            prevTag = ''
            prevVerb = ''
            while i < len(words):
                word, tag = words[i]
                if tag in ['PEO','ORG']:
                    if prevNER and prevVerb:
                        if ((prevNER.strip()+' ('+prevVerb.strip()+') '+word.strip()) not in relationDict) and tag != prevTag:
                            relationDict[prevNER.strip()+' ('+prevVerb.strip()+') '+word.strip()].append(currTimeString)
                    prevNER = word
                    prevTag = tag
                    prevVerb = ''
                if tag in ('v', 'vd', 'vshi', 'vyou', 'vl', 'vi'):
                    prevVerb += word
                i += 1

        writeList1 = [orgList, titleDict, relationDict]
        writeList2 = ['机构', '人物', '关系对']

        if financialDict:
            writeList1.append(financialDict)
            writeList2.append('投融资、合作信息')

        saveToTxt(title, writeList1, writeList2, fileName=fileName)
        ##
        # return senDict, nameDict, peopleList, orgList, undfList
        return [orgList, titleDict, relationDict]
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
            helper(title, content, description, contentMode, useExpanded, accurateMode, dirName + '/' + 'PO_' + title + '.txt')
    else:
        title = crawlResults[0][0]
        content = crawlResults[1][0]
        description = crawlResults[2][0] if crawlResults[2] else ''
        helper(title, content, description, contentMode, useExpanded, accurateMode, dirName + '/' + 'PO_' + title + '.txt')

if __name__ == "__main__":
    # 长文章，给定url提取
    NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-10-25-8')
    # NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-08-16')
    # NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-08-8')
    # NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-11-20-5')

    # AI Daily 类型文章，给定url提取
    # NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies/2f2d4ee1-9486-4aa5-84fa-fd76f2ae7239', dirName='outputs/AIDailyByURL tests')
    # NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies/bfcb0416-1695-4a08-95b3-b00208f7271d', dirName='outputs/AIDailyByURL tests')
    # NER_PO('AIDaily', 'https://www.jiqizhixin.com/dailies?id=62a92b37-6f86-4798-ae65-3d9fad8dabaf', dirName='outputs/AIDailyByURL tests')

    # AI Daily类型文章，自动提取
    # NER_PO('AIDaily', autoCrawlAI=True, articleNumberAI=5, dirName='outputs/AIDailyAuto tests')






