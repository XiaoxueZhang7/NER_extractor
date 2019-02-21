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
from loadTools import *


def NER_PP(articleType, articleUrl='', autoCrawlAI=False, articleNumberAI=10, paperMode=[1,1,1], useExpanded=[0,0,1], accurateMode=False, dirName='outputs'):
    '''
    input:  articleType: string, 'AIDaily' or other, case insensitive;
            articleUrl: string, default to '';
            autoCrawlAI: boolean, only work when articleType='AI Daily', default to True;
            articleNumberAI: int, only work when articleType='AI Daily' and autoCrawlAI=True, default to 10;
            paperMode: list of int indicating methods used to extract paper, 1 for use, 0 for ignore. 3 digits stand for: [keyWord, specialSymbel, english]
            useExpanded: whether or not to use expanded words, 1 for use, 0 for not, 3 digits stand for: [organization, people, undefined]
            accurateMode: whether or not to use StanfordNERTagger, which is more accurate but computationaly more expensive.
            dirName: string, deafult to 'test.txt'
    output: a txt file with organization, people, relations printed
    '''

    paperKeyWords = ['paper', '论文']
    symbelKeyWords = [['“', '”'], ['‘', '’'], ['《', '》'], ['「', '」']]
    confKeyWords = ['大会','会议','论坛','Interface','沙龙']
    pruneKeyWords = ['链接']
    authorKeyWords = ['作者']
    specialN = ['nr','ns','nt','nz','nl','ng','nrt','nrfg', 'ENG-ORG', 'ENG-PEO']
    lastNameDict = txtToDict("../docs/last name.txt")
    StanfordTagger = StanfordNERTagger('../docs/stanford-ner-2014-08-27/classifiers/english.all.3class.distsim.crf.ser.gz', '../docs/stanford-ner-2014-08-27/stanford-ner.jar')
    
    def helper(title, content, items, paperMode, useExpanded, accurateMode, fileName):
        if not containKeyWords((title+content).decode('utf-8'), paperKeyWords) and not containKeyWords((title+content).decode('utf-8'), [''.join(i) for i in symbelKeyWords]):
            print 'No paper included in this article.'
            return
            
        sentences = splitSentence(title, content, '')
        paperSentences = defaultdict(set)
        listOfContentDict = []
        listOfName = []
        paperList = []


        candidateList = []

        for currSen in sentences:
            currCandidatesList = []
            currAuthorsList = []
            if containKeyWords(currSen, pruneKeyWords):
                currSen,_  = pruneSentence(currSen, containKeyWords(currSen, pruneKeyWords))
            if containKeyWords(currSen, authorKeyWords):
                currSen,authorsByKeyWords = pruneSentence(currSen, containKeyWords(currSen, authorKeyWords))
                if '、'.decode('utf-8') in authorsByKeyWords:
                    currAuthorsList += authorsByKeyWords.split('、'.decode('utf-8'))
                if ','.decode('utf-8') in authorsByKeyWords:
                    currAuthorsList += authorsByKeyWords.split(','.decode('utf-8'))
                '''
                authorsByKeyWords = findPapersByKeyWords(currSen, authorKeyWords, mode=[0,1])[0]
                    currSen = re.sub(authorsByKeyWords, '', currSen)
                    for keyWord in authorKeyWords:
                        authorsByKeyWords = re.sub(keyWord.decode('utf-8'), '', authorsByKeyWords)
                    if ','.decode('utf-8') in authorsByKeyWords:
                        currAuthorsList += authorsByKeyWords.split(','.decode('utf-8'))
                    elif '、'.decode('utf-8') in authorsByKeyWords:
                        currAuthorsList += authorsByKeyWords.split('、'.decode('utf-8'))
                '''
            words = generatorToList(pseg.cut(currSen))

            if 'nr' in [tag for word,tag in words]:
                currAuthorsList += [word for word,tag in words if tag=='nr']
                for author in currAuthorsList:
                    currSen = re.sub(author, '', currSen, flags=re.M|re.I|re.S)
            if containKeyWords(currSen, [symbles[0] for symbles in symbelKeyWords]):
                currSen, papersBySymble = findPapersBySymbel(currSen, symbelKeyWords)
                currCandidatesList += [[paper, 2] for paper in papersBySymble]
            if containKeyWords(currSen, confKeyWords):
                currCandidatesList += [[paper, 0] for paper in findPapersByKeyWords(currSen, confKeyWords)]
            if containKeyWords(currSen, paperKeyWords):
                currCandidatesList += [[paper, 1] for paper in findPapersByKeyWords(currSen, paperKeyWords)]
            words = generatorToList(pseg.cut(currSen))
            currCandidatesList += [[paper, 3] for paper in findPapersByEng(words)]
            candidateList.append([currCandidatesList, currAuthorsList])


        paperDict = defaultdict(list)
        confDict = []
        organizationDict = []
        peopleDict = []

        for pairs, finalAuthorsList in candidateList:
            finalPapersList = []
            for pair in pairs:
                if pair[1] == 0:
                    confDict.append(re.sub('[。？！……（）——：，、]'.decode('utf-8'), '', pair[0]).strip())
                elif pair[1] == 1:
                    finalPapersList.append(pair[0].strip())
                else:
                    if len(pair[0].split(' ')) > 4:
                        finalPapersList.append(pair[0].strip())
                    else:
                        engCandidates = splitSentence('',pair[0].encode('utf-8'),'',endings=u',.，。')  
                        for engCandidate in engCandidates:  
                            engWords = generatorToList(pseg.cut(engCandidate))        
                            if 'CONF' in [tag for word,tag in engWords]:
                                for word in [word for word,tag in words if tag == 'CONF']:
                                    confDict.append(re.sub('[。？！……（）——：，、]'.decode('utf-8'), '', word).strip())
                                    continue
                            tag = engTagging(engCandidate, accurateMode, StanfordTagger)
                            if tag == 1:
                                finalAuthorsList.append(engCandidate.strip())
                            elif tag == 0:
                                organizationDict.append(re.sub('[。？！……（）——：，、]'.decode('utf-8'), '', engCandidate).strip())
            peopleDict += finalAuthorsList
            for paper in finalPapersList:
                if paper.strip() not in paperDict:
                    paperDict[re.sub('[。？！……（）——：，、]'.decode('utf-8'), '', paper).strip()] += list(set(finalAuthorsList))
        # 集合类文章：
        if containKeyWords(title.decode('utf-8'), ['精选','推荐','列表','篇','排名','总结','集合','合集','清单','最佳']):
            paperItems = defaultdict(set)
            for entry in items:
                currAuthors = []
                currPapers = []
                entry = entry.decode('utf-8')
                if containKeyWords(entry, pruneKeyWords):
                    entry,_ = pruneSentence(entry, containKeyWords(entry, pruneKeyWords))
                if containKeyWords(entry, authorKeyWords):
                    authorsByKeyWords,entry = pruneSentence(entry, containKeyWords(entry, authorKeyWords))
                    '''
                    authorsByKeyWords = findPapersByKeyWords(entry, authorKeyWords, mode=[0,1])
                    entry = re.sub(authorsByKeyWords, '', entry)
                    for keyWord in authorKeyWords:
                        authorsByKeyWords = re.sub(keyWord.decode('utf-8'), '', authorsByKeyWords)[0]
                    if ','.decode('utf-8') in authorsByKeyWords:
                        currAuthors += authorsByKeyWords.split(','.decode('utf-8'))
                    elif '、'.decode('utf-8') in authorsByKeyWords:
                        currAuthors += authorsByKeyWords.split('、'.decode('utf-8'))
                    '''
                    if '、'.decode('utf-8') in authorsByKeyWords:
                        currAuthors += authorsByKeyWords.split('、'.decode('utf-8'))
                        peopleDict += authorsByKeyWords.split('、'.decode('utf-8'))
                    if ','.decode('utf-8') in authorsByKeyWords:
                        currAuthors += authorsByKeyWords.split(','.decode('utf-8'))
                        peopleDict += authorsByKeyWords.split(','.decode('utf-8'))
                entry = entry.encode('utf-8')
                sens = splitSentence('',entry,'',endings=u',.，。')

                for sen in sens:
                    words = generatorToList(pseg.cut(sen))
                    if 'nr' in [tag for word,tag in words]:
                        currAuthors = [word for word,tag in words if tag=='nr']
                        for author in currAuthors:
                            print 'nr:', author
                            sen = re.sub(author, '', sen, flags=re.M|re.I|re.S)
                    if containKeyWords(sen, paperKeyWords):
                        paperByKeyWords = findPapersByKeyWords(sen, paperKeyWords)
                        for paper in paperByKeyWords:
                            currPapers.append(paper.strip())
                            sen = re.sub(paper,'',sen)
                    paperList = findPapersByEng(generatorToList(pseg.cut(sen)))
                    for paper in paperList:
                        if len(paper.split(' ')) > 4:
                            currPapers.append(paper.strip())
                        elif engTagging(paper, accurateMode, StanfordTagger) == 1:
                            currAuthors.append(paper.strip())
                            peopleDict.append(paper.strip())
                        elif engTagging(paper, accurateMode, StanfordTagger) == 0:
                            organizationDict.append(paper.strip())
                for paper in currPapers:
                    paperDict[re.sub('[。？！……（）——：，、]'.decode('utf-8'), '', paper).strip()] = currAuthors
            


        listOfName.append('会议'.decode('utf-8'))
        listOfContentDict.append(confDict)
        #listOfName.append('机构'.decode('utf-8'))
        #listOfContentDict.append(organizationDict)
        listOfName.append('论文标题'.decode('utf-8'))
        listOfContentDict.append(paperDict)
        listOfName.append('人物'.decode('utf-8'))
        listOfContentDict.append(peopleDict)

        saveToTxt(title, listOfContentDict, listOfName, fileName)

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
            items = ''
            helper(title, content, items, paperMode, useExpanded, accurateMode, dirName+'/'+'PP_'+title+'.txt')
    else:
        title = crawlResults[0][0]
        content = crawlResults[1][0]
        items = crawlResults[2][0] if crawlResults[2] else ''
        helper(title, content, items, paperMode, useExpanded, accurateMode, dirName+'/'+'PP_'+title+'.txt')

if __name__ == "__main__":
    # 长文章，给定url提取
    NER_PP('资讯', 'https://www.jiqizhixin.com/articles/2018-10-25-8')
    #NER_PP('资讯', 'https://www.jiqizhixin.com/articles/2018-12-04-2')
    #NER_PP('资讯', 'https://www.jiqizhixin.com/articles/2018-08-27-11?from=synced&keyword=%E8%AE%BA%E6%96%87')
    #NER_PP('资讯', 'https://www.jiqizhixin.com/articles/2018-12-11-24?from=synced&keyword=%E8%AE%BA%E6%96%87')

    
    # AI Daily 类型文章，给定url提取
    #NER_PP('AIDaily', 'https://www.jiqizhixin.com/dailies/fed1f6cc-bc83-465c-8293-fb1e4f089538', dirName='outputs/AIDailyByURL tests')


    # AI Daily类型文章，自动提取
    #NER_PP('AIDaily', autoCrawlAI=True, articleNumberAI=6, dirName='outputs/AIDailyAuto tests')
