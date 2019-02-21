# -*- coding: utf-8 -*

import jieba.posseg as pseg
import jieba
import re
import os
from collections import defaultdict
from nltk import pos_tag, word_tokenize, sent_tokenize
from nltk.tag.stanford import StanfordNERTagger

from crawlTools import *
from namedEntityTools import *
#from loadTools import *


def NER_OO(articleType, articleUrl='', autoCrawlAI=False, articleNumberAI=10, orgMode=[0,0,0], useExpanded=[0,0,1], accurateMode=False, dirName='outputs'):
    '''
    input:  articleType: string, 'AIDaily' or other, case insensitive;
            articleUrl: string, default to '';
            autoCrawlAI: boolean, only work when articleType='AI Daily', default to True;
            articleNumberAI: int, only work when articleType='AI Daily' and autoCrawlAI=True, default to 10;
            orgMode: list of int indicating whether or not to search for organization names, 1 for search, 0 for not. 3 digits stand for: [before key word, after key word, ]
            useExpanded: whether or not to use expanded words, 1 for use, 0 for not, 3 digits stand for: [organization, people, undefined]
            dirName: string, deafult to 'test.txt'
    output: a txt file with organization, people, relations printed
    '''

    investKeyWords = ['融资','领投','跟投','收购','合并','投资','创投','获投','注资','并购','参投','出资','斥资','筹资','筹集','入股','增持']
    cooporationKeyWords = ['合作','结盟','联合','对接','携手','提供商','供应商','联盟','联手','牵手','共建']
    specialN = ['nr','ns','nt','nz','nl','ng','nrt','nrfg', 'ENG-ORG', 'ENG-PEO']
    lastNameDict = txtToDict("../docs/last name.txt")
    StanfordTagger = StanfordNERTagger('../docs/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz', '../docs/stanford-ner-2014-08-27/stanford-ner.jar')
    def helper(title, content, items, orgMode, useExpanded, accurateMode, fileName):

        if not containKeyWords((title+content).decode('utf-8'), investKeyWords+cooporationKeyWords):
            print 'No investment relation included in this article.'
            return
            
        sentences = splitSentence(title, content, '')
        paperSentences = defaultdict(set)
        informationList = []
        numberSet = set([])
        roundSet = set([])
        ##
        senDict = defaultdict(list)
        ##

        #提轮次：
        if containKeyWords((title+content).decode('utf-8'), ['轮']):
            roundList = re.findall('[A-Za-z0-9-\+\- ]+'.decode('utf-8')+'轮'.decode('utf-8'), (title+content).decode('utf-8'), flags=re.M|re.I|re.S)
            for round in roundList:
                roundSet.add(re.sub('[ ，；。？！……]'.decode('utf-8'), '', round))



        for sen in sentences:
            words = generatorToList(pseg.cut(sen))
            verbList = containKeyWords(sen, investKeyWords+cooporationKeyWords)
            if verbList:
                senDict[sen.strip()] = verbList
            
            #提数字：
            if 'm' in [word[1] for word in words]:
                numberList = findNumber(words)
                for number in numberList:
                    if re.sub('[^A-Za-z0-9]'.decode('utf-8'), '', number):
                        numberSet.add(re.sub('[. ，；。、？！……\|\[\]\(\)\'\"——：©]'.decode('utf-8'), '', number))
            for verb in verbList:
                prev, next = divideSentence(sen, verb)
                if orgMode[0]:
                    org1 = findOrg(generatorToList(pseg.cut(prev)), specialN, useExpanded, lastNameDict, accurateMode, StanfordTagger)
                else:
                    org1 = [prev]

                if orgMode[1]:
                    org2 = findOrg(generatorToList(pseg.cut(next)), specialN, useExpanded, lastNameDict, accurateMode, StanfordTagger)
                else:
                    org2 = [next]

                if (not org1 and len(org2)==2):
                    org1 = [org2[0]]
                    org2 = [org2[1]]

                if (not org2 and len(org1)==2):
                    org2 = [org1[1]]
                    org1 = [org1[0]]
                org1 = [''] if (not org1 and org2) else org1
                org2 = [''] if (not org2 and org1) else org2

                for o1 in org1:
                    for o2 in org2:
                        informationList.append(o1+' <<'.decode('utf-8')+verb.decode('utf-8')+'>> '.decode('utf-8')+o2)
        ##
        return senDict
        ##
        saveToTxt(title, [roundSet,informationList,numberSet], ['轮次信息'.decode('utf-8'),'投融资信息'.decode('utf-8'),'金额、日期等信息'.decode('utf-8')], fileName)


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
            items = []
            return helper(title, content, items, orgMode, useExpanded, accurateMode, dirName+'/'+'OO_'+title+'.txt')
    else:
        title = crawlResults[0][0]
        content = crawlResults[1][0]
        items = crawlResults[2] if crawlResults[2] else []
        return helper(title, content, items, orgMode, useExpanded, accurateMode, dirName+'/'+'OO_'+title+'.txt')

if __name__ == "__main__":
    # 长文章，给定url提取
    NER_OO('资讯', 'https://www.jiqizhixin.com/articles/2018-10-25-8')

    # AI Daily 类型文章，给定url提取
    #NER_OO('AIDaily', 'https://www.jiqizhixin.com/dailies?id=fdb69845-3954-4db8-be94-aeefcc36e4c9', dirName='outputs/AIDailyByURL tests')
    #NER_OO('AIDaily', 'https://www.jiqizhixin.com/dailies/f6146e87-2565-4bb2-bec5-e8d4a410f8e3', dirName='outputs/AIDailyByURL tests')
    #NER_OO('AIDaily', 'https://www.jiqizhixin.com/dailies/2126d50f-af41-4490-90ed-e3bc6ca54667', dirName='outputs/AIDailyByURL tests')
    #NER_OO('AIDaily', 'https://www.jiqizhixin.com/dailies/b036c946-2421-4541-8d99-ee093bd4e24b', dirName='outputs/AIDailyByURL tests')

    # AI Daily类型文章，自动提取
    #NER_OO('AIDaily', autoCrawlAI=True, articleNumberAI=10, dirName='outputs/AIDailyAuto tests')
