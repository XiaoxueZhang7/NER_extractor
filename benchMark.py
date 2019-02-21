# -*- coding: utf-8 -*
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
from collections import defaultdict



from NER_PO import *
from crawlTools import *
from namedEntityTools import *

pattern = '[.,:;，、。：；？（）“”‘’\<\>\{\}\(\)\[\]\"\'\-\_\+\=]'.decode('utf-8')
def initializeDict(fileName):
    df = pd.read_excel(fileName, sheetname='Sheet1')
    print ('loading answers:')
    print ('length of excel file: ', len(df))
    print ('Column headings: ', df.columns)
    # sentenceDict[sen]: [dictOfNames(name, tag), dictOfVerb(verb, tag)]
    sentenceDict = defaultdict(list)
    nameDict = defaultdict(str)
    sentenceList = []
    peopleList = []
    orgList = []
    for index, row in df.iterrows():
        trimmed = re.sub(pattern, '', row[u'句子'])
        if trimmed not in sentenceList:
            sentenceList.append(trimmed)
        sentenceDict[trimmed] = []

        dictOfNames = defaultdict(str)
        dictOfVerb = defaultdict(str)

        if not pd.isnull(row[u'人名']):
            li = re.split('，'.decode('utf-8'), row[u'人名'])
            for l in li:
                dictOfNames[l] = 'P'
                nameDict[l] = 'P'
                peopleList.append(l)
        if not pd.isnull(row[u'机构名']):
            li = re.split('，'.decode('utf-8'), row[u'机构名'])
            for l in li:
                dictOfNames[l] = 'O'
                nameDict[l] = 'O'
                orgList.append(l)
        if not pd.isnull(row[u'金融动作']):
            li = re.split('，'.decode('utf-8'), row[u'金融动作'])
            for l in li:
                dictOfVerb[l] = 'F'

        sentenceDict[trimmed] = [dictOfNames, dictOfVerb, nameDict]

        #sentenceDict[trimmed].append(row[u'人名数量'])
        #sentenceDict[trimmed].append(row[u'机构名数量'])
        #sentenceDict[trimmed].append(row[u'金融动作数量'])
    #print 'number of sentences: ', len(sentenceDict), len(sentenceList)
    return sentenceDict, sentenceList, nameDict, peopleList, orgList



# test out different scorers
def points(test, answer, keyList):
    #print 'ratio: ', fuzz.ratio(test, answer)
    #print 'partial_ratio: ', fuzz.partial_ratio(test, answer)
    #print 'token_sort_ratio: ', fuzz.token_sort_ratio(test, answer)
    #print 'token_set_ratio: ', fuzz.token_set_ratio(test, answer)
    print ('choice: ', process.extractOne(test, keyList)[0])



def transform(fileName):
    df = pd.read_table(fileName, delim_whitespace=True)
    nameDict = defaultdict(defaultdict)
    peopleList = []
    orgList = []
    undfList = []
    f = open(fileName, "r")
    tag = 'P'
    for name in f:
        if name.lower().strip() in ['people', 'undefined', 'organization']:
            tag = name[0].upper()
        else:
            nameDict[name.decode('utf-8')] = tag
            if tag == 'P':
                peopleList.append(name.decode('utf-8'))
            elif tag == 'O':
                orgList.append(name.decode('utf-8'))
            else:
                undfList.append(name.decode('utf-8'))
    f.close()
    return nameDict, peopleList, orgList, undfList



# resultDict: key: sen.decode()
#             val: dict: name: tag
def sentenceScorer(resultDict, sentenceDict, sentenceList, scorer=1, misLabel=0.8, unLabel=0.9):
    totalScore = 0
    totalCount = len(resultDict)
    for orgSen, nameDict in resultDict.iteritems():
        orgSen = re.sub(pattern, '', orgSen)
        sen = process.extractOne(orgSen, sentenceList, scorer = fuzz.partial_ratio)[0]
        dictOfNames, dictOfVerb, _ = sentenceDict[sen]

        currPoint = 0
        count = len(dictOfNames)
        if count == 0:
            totalCount -= 1
            continue

        for name in dictOfNames:
            if nameDict:
                match = process.extractOne(name, nameDict.keys(), scorer = fuzz.partial_ratio)[0]
                point = fuzz.ratio(name, match) if scorer == 0 else fuzz.partial_ratio(name, match)
                if point == 0:
                    continue
                if dictOfNames[name] == nameDict[match]:
                    currPoint += point
                elif nameDict[match] == 'U':
                    currPoint += point * unLabel
                else:
                    currPoint += point * misLabel


        totalScore += float(currPoint/count)
    print ('average precision in each sentence is: '+str(float(totalScore/totalCount))+'%')



def overAllScorer(OriginalList, AnswerList, scorer=0, misLabel=0.8, unLabel=0.9, exact=True):
    # precision
    currScore = 0
    currCount = len(OriginalList)
    for name in OriginalList:
        match = process.extractOne(name, AnswerList, scorer=fuzz.partial_ratio)[0]
        point = fuzz.ratio(name, match) if scorer == 0 else fuzz.partial_ratio(name, match)
        currScore += point
    print ('precision on extract Named Entities '+'is: '+str(float(currScore/currCount))+'%')

    # recall
    currScore = 0
    currCount = len(AnswerList)
    for name in AnswerList:
        match = process.extractOne(name, OriginalList, scorer=fuzz.partial_ratio)[0]
        point = fuzz.ratio(name, match) if scorer == 0 else fuzz.partial_ratio(name, match)
        if exact and int(point) == 100:
            currScore += point
        elif not exact:
            currScore += point
    print ('recall on extract Named Entities '+'is: '+str(float(currScore/currCount))+'%')




def catagorizeScorer(OriginalLists, AnswerLists, scorer=0, misLabel=0.8, unLabel=0.9, exact=True):
    tags = ['P','O','U']
    # precision
    for i in range(len(OriginalLists)):
        OcurrList = OriginalLists[i]
        AcurrList = AnswerLists[i]
        tag = tags[i]
        currScore = 0
        currCount = len(OcurrList)
        for name in OcurrList:
            match = process.extractOne(name, AcurrList, scorer=fuzz.partial_ratio)[0]
            point = fuzz.ratio(name, match) if scorer == 0 else fuzz.partial_ratio(name, match)
            if exact and int(point) == 100:
                currScore += point
            elif not exact:
                currScore += point
        print ('precision on extract ('+tag+') taged words '+'is: '+str(float(currScore/currCount))+'%')

    # recall
    for i in range(len(AnswerLists)):
        AcurrList = AnswerLists[i]
        OcurrList = OriginalLists[i] if i<2 else OriginalLists[0]+OriginalLists[1]
        tag = tags[i]
        currScore = 0
        currCount = len(AcurrList)
        for name in AcurrList:
            match = process.extractOne(name, OcurrList, scorer=fuzz.partial_ratio)[0]
            point = fuzz.ratio(name, match) if scorer == 0 else fuzz.partial_ratio(name, match)
            if exact and int(point) == 100:
                currScore += point
            elif not exact:
                currScore += point
        print ('recall on extract ('+tag+') taged words '+'is: '+str(float(currScore/currCount))+'%')


def initializeRelationDict(fileName):
    df = pd.read_excel(fileName, sheetname='Sheet1')
    print ('loading answers:')
    print ('length of excel file: ', len(df))
    print ('Column headings: ', df.columns)
    # sentenceDict[sen]: [dictOfNames(name, tag), dictOfVerb(verb, tag)]
    relationDict = defaultdict(list)
    nameDict = defaultdict(str)
    actionList = []
    sentenceList = []
    otherList = []
    outputList = []

    for index, row in df.iterrows():
        trimmed = re.sub(pattern, '', row[u'句子'])
        relationDict[trimmed] = []
        currAction = []
        currName1 = []
        currName2 = []
        currOthers = []
        currOutput = []

        if not pd.isnull(row[u'输出']):
            output = re.sub(pattern, '', row[u'输出'])
            outputList.append(output)
            currOutput.append(output)
        if not pd.isnull(row[u'动作']):
            li = re.split('、'.decode('utf-8'), row[u'动作'])
            for l in li:
                actionList.append(l)
                currAction.append(l)
        if not pd.isnull(row[u'主体1']):
            li = re.split('、'.decode('utf-8'), row[u'主体1'])
            for l in li:
                nameDict[l] = '1'
                currName1.append(l)
        if not pd.isnull(row[u'主体2']):
            li = re.split('、'.decode('utf-8'), row[u'主体2'])
            for l in li:
                nameDict[l] = '2'
                currName2.append(l)
        if not pd.isnull(row[u'其他']):
            li = re.split('、'.decode('utf-8'), row[u'其他'])
            for l in li:
                otherList.append(l.strip())
                currOthers.append(l)


        relationDict[trimmed] = [currOutput, currAction, currName1, currName2, currOthers]

    return relationDict, outputList, nameDict, actionList, otherList

def relationScorer(OrelationDict, OnameDict, OactionList, OotherList, AsenDict, scorer=0, misLabel=0.8, unLabel=0.9, exact=True):
    totalScore = 0

    #precision
    totalCount = len(OrelationDict)
    outputScore = 0
    actionScore = 0
    actionCount = 0
    nameScore = 0
    nameCount = 0

    for orgSen, values in OrelationDict.iteritems():
        orgSen = re.sub(pattern, '', orgSen)
        sen = process.extractOne(orgSen, AsenDict.keys(), scorer = fuzz.partial_ratio)[0]
        Ooutput, Oaction, Oname1, Oname2, Oothers = values
        if sen not in AsenDict or len(AsenDict[sen]) == 0:
            continue
        Aoutput, Aaction, Anames = AsenDict[sen]

        # 1
        outputScore += fuzz.ratio(Ooutput, Aoutput) if scorer == 0 else fuzz.partial_ratio(Ooutput, Aoutput)

        # 2
        if Oaction:
            actionCount += 1
            currActionScore = 0
            for a in Oaction:
                aa = process.extractOne(a, Aaction, scorer = fuzz.partial_ratio)[0] if Aaction else ''
                point = fuzz.ratio(a, aa) if scorer == 0 else fuzz.partial_ratio(a, aa)
                if exact and int(point) == 100:
                    currActionScore += point
                elif not exact:
                    currActionScore += point
            actionScore += float(currActionScore/len(Oaction))
        # 3
        if Oname1+Oname2:
            nameCount += 1
            currNameScore = 0
            for n in Oname1+Oname2:
                nn = process.extractOne(a, Anames, scorer = fuzz.partial_ratio)[0] if Anames else ''
                point = fuzz.ratio(n, nn) if scorer == 0 else fuzz.partial_ratio(n, nn)
                if exact and int(point) == 100:
                    currNameScore += point
                elif not exact:
                    currNameScore += point
            nameScore += float(currNameScore/(len(Oname1)+len(Oname2)))

    print ('Precision on output relational sentence is: '+str(int(outputScore/totalCount))+'%')
    print ('Precision on extract relational actions is: '+str(int(actionScore/actionCount))+'%')
    print ('Precision on extract relational NER is: '+str(int(nameScore/nameCount))+'%')



    #recall
    totalCount = len(AsenDict)
    outputScore = 0
    actionScore = 0
    actionCount = 0
    nameScore = 0
    nameCount = 0

    for ansSen, values in AsenDict.iteritems():
        ansSen = re.sub(pattern, '', ansSen)
        sen = process.extractOne(ansSen, OrelationDict.keys(), scorer = fuzz.partial_ratio)[0]
        Aoutput, Aaction, Anames = values
        if sen not in OrelationDict:
            continue
        Ooutput, Oaction, Oname1, Oname2, Oothers = OrelationDict[sen]

        # 1
        outputScore += fuzz.ratio(Ooutput, Aoutput) if scorer == 0 else fuzz.partial_ratio(Ooutput, Aoutput)

        # 2
        if Aaction:
            actionCount += 1
            currActionScore = 0
            for a in Aaction:
                aa = process.extractOne(a, Oaction, scorer = fuzz.partial_ratio)[0] if Oaction else ''
                point = fuzz.ratio(a, aa) if scorer == 0 else fuzz.partial_ratio(a, aa)
                if exact and int(point) == 100:
                    currActionScore += point
                elif not exact:
                    currActionScore += point
            actionScore += float(currActionScore/len(Aaction))
        # 3
        if Anames:
            nameCount += 1
            currNameScore = 0
            for n in Anames:
                nn = process.extractOne(a, Oname1+Oname2, scorer = fuzz.partial_ratio)[0] if Oname1+Oname2 else ''
                point = fuzz.ratio(n, nn) if scorer == 0 else fuzz.partial_ratio(n, nn)
                if exact and int(point) == 100:
                    currNameScore += point
                elif not exact:
                    currNameScore += point
            nameScore += float(currNameScore/len(Anames))

    print ('Recall on output relational sentence is: '+str(int(outputScore/totalCount))+'%')
    print ('Recall on extract relational actions is: '+str(int(actionScore/actionCount))+'%')
    print ('Recall on extract relational NER is: '+str(int(nameScore/nameCount))+'%')



if __name__ == "__main__":
    OrelationDict, OoutputList, OnameDict, OactionList, OotherList = initializeRelationDict('docs/relationStandards.xlsx')


    AsenDict = NER_PO('资讯', 'https://www.jiqizhixin.com/articles/2018-10-25-8', useExpanded=[1,0,1])
    print ('===== '+' jieba '+' 关系测试'+'exactScorer=True'+' useExpanded=[1,0,1] '+' accurateMode=False '+' =====')
    relationScorer(OrelationDict, OnameDict, OactionList, OotherList, AsenDict)



