# -*- coding: utf-8 -*
import pyltp
from pyltp import SentenceSplitter
import jieba.posseg as pseg
import jieba
import re
import os
import sys
from collections import defaultdict
from nltk import pos_tag, word_tokenize, sent_tokenize, ne_chunk
from nltk.tag.stanford import StanfordNERTagger

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
    specialN = ['nr', 'ns', 'nt', 'nz', 'nl', 'ng', 'nrt', 'nrfg', 'vn', 'CONF']
    engSpecialN = ['eng','CONF','x','m','w']
    tagInterpret = ['ORG', 'PEO', 'O']
    lastNameDict = txtToDict("docs/last name.txt")
    StanfordTagger = StanfordNERTagger('docs/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz','docs/stanford-ner-2014-08-27/stanford-ner.jar')
    titleList = createDict('docs/titles.txt')
    loadDicts(investKeyWords + cooporationKeyWords)

    def helper(title, content, description, contentMode, useExpanded, accurateMode, fileName):
        #sentences = splitSentence(title, content, description, contentMode)
        sentences = SentenceSplitter.split(title+content)
        peopleList = []
        orgList = []
        relationList = []
        financialList = []
        titleDict = defaultdict(list)
        peopleList, _, orgList = zh_NER_TF_master(title+content)
        peopleList = list(set(peopleList))
        orgList = list(set(orgList))

        for sen in sentences:
            currPeople = containKeyWords(sen, peopleList)
            currOrg = containKeyWords(sen, orgList)
            currTitle = containKeyWords(sen, titleList)
            keyWords = []
            verbList = containKeyWords(sen, investKeyWords + cooporationKeyWords)
            currRoundList = getRound(sen)
            currRoundString = '; 轮次: ' + ''.join(currRoundList) if ''.join(currRoundList).strip() else ''


            if (not currPeople and currOrg) and (not verbList):
                continue
            PEOList = []
            TTLList = []
            ORGList = []
            for word in currPeople:
                it = re.finditer(word, sen.lower())
                for target in it:
                    if not isPeople(word, lastNameDict):
                        continue
                    keyWords.append([(target.start(), target.end()), 'PEO', word])
                    PEOList.append([(target.start(), target.end()), word])
            for word in currOrg:
                it = re.finditer(word, sen.lower())
                for target in it:
                    keyWords.append([(target.start(), target.end()), 'ORG', word])
                    ORGList.append([(target.start(), target.end()), word])
            for word in currTitle:
                it = re.finditer(word, sen.lower())
                for target in it:
                    keyWords.append([(target.start(), target.end()), 'TTL', word])
                    TTLList.append([(target.start(), target.end()), word])

            # jieba标注其他词
            sortedKeyWords = sorted(keyWords, key = lambda k:k[0][0])
            prev = 0
            words = []
            for interval, tag, word in sortedKeyWords:
                words += generatorToList(pseg.cut(sen[prev:interval[0]]))
                words += [[word, tag]]
                prev = interval[1]
            words += generatorToList(pseg.cut(sen[prev:]))

            #print ('sen', sen)
            #print ('words',words)

            # merging and tagging eng words
            i = 0
            while i < len(words):
                word, tag = words[i]
                if tag == 'eng':
                    start, end, expandedWord = expandNoun(i, words, engSpecialN)
                    words[i][0] = expandedWord
                    words[i][1] = tagInterpret[engTagging(expandedWord, accurateMode, StanfordTagger)]
                    if words[i][1] == 'PEO':
                        peopleList.append(expandedWord)
                        titleDict[expandedWord.strip()] = []
                    if words[i][1] == 'ORG':
                        orgList.append(expandedWord)

                    i = end
                else:
                    i += 1

            currMoneyList = [num for num in findNumber(words) if containKeyWords(num, ['亿', '元', '万'])]
            currMoneyString = '; 金额: ' + ''.join(currMoneyList) if ''.join(currMoneyList).strip() else ''
            currTimeList = [num for num in findNumber(words) if containKeyWords(num, ['月', '日', '年'])]
            currTimeString = '; 时间: ' + ''.join(currTimeList) if ''.join(currTimeList).strip() else ''

            # 匹配职位信息
            for _, p in PEOList:
                titleDict[p.strip()] = []
            titleDict = trimTitle(pairTitle(PEOList, TTLList, ORGList, words, titleDict, currTimeString))


            # 找金融动作
            #findFinancialRelation(verbs, sen, ORGList
            financialWords = [k for k in words if k[1] in ['ORG','FNC','x']]
            findFinancialRelation(financialWords, financialList,currRoundString,currMoneyString,currTimeString)


            # 找动词
            i = 0
            prevNER = ''
            prevTag = ''
            prevVerb = ''
            while i < len(words):
                word, tag = words[i]
                if tag in ['PEO','ORG']:
                    if prevNER and prevVerb:
                        if (prevNER.strip()+' ('+prevVerb.strip()+') '+word.strip()+currTimeString not in relationList) and tag != prevTag:
                            relationList.append(prevNER.strip()+' ('+prevVerb.strip()+') '+word.strip()+currTimeString)
                    prevNER = word
                    prevTag = tag
                    prevVerb = ''
                if tag in ('v', 'vn'):
                    prevVerb += word
                i += 1


        writeList1 = [orgList, titleDict, relationList]
        writeList2 = ['机构', '人物', '关系对']
        if financialList:
            writeList1.append(financialList)
            writeList2.append('投融资、合作信息')


        saveToTxt(title, writeList1, writeList2, fileName=fileName)
        ##
        # return senDict, nameDict, peopleList, orgList, undfList
        return [orgList, titleDict, relationList]
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






