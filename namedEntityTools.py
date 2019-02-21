# functions used in main extractNames unction
# -*- coding: utf-8 -*

# Split 'content' by sentence. Parameter contentMode is 3-bit long, each bit represents whether or not to include title, content or description. 0 for not include, 1 for include.
import sys
import re
import nltk
from collections import defaultdict
from nltk import pos_tag, word_tokenize, sent_tokenize, ne_chunk
from nltk.tag.stanford import StanfordNERTagger

def splitSentence(title, content, description, contentMode=[1,1,0], endings=u'。？！……'):
    '''
    input:  title:     string, before
            content:   string, before
            contentMode:      list of int, 1 for use, 0 for ignore. 3 digits stand for: [title, content, description]
    output: sentences: list of strings, after
    '''
    sentences = []
    if contentMode[0] == 1:
        sentences.append(title)
        
    if contentMode[1] == 1:
        curr = ''
        contentD = content
        for i in range(len(contentD)):
            if contentD[i] == '\n':
                continue
            elif contentD[i] in endings:
                sentences.append(curr)
                curr = ''
            else:
                curr += contentD[i]
        sentences.append(curr)
    if contentMode[2] == 1:
        curr = ''
        descriptionD = description
        for i in range(len(descriptionD)):
            if descriptionD[i] == '\n':
                continue
            elif descriptionD[i] in endings:
                sentences.append(curr)
                curr = ''
            else:
                curr += descriptionD[i]
        sentences.append(curr)
    return sentences

# expand special nouns
def expandNoun(i, words, specialN):
    # english words:
    start, end = i, i
    if words[i][1] in ['eng','ENG-PEO','ENG-ORG','CONF']:
        name = words[i][0]
        end += 1
        start -= 1
        while start >= 0 and (words[start][0] in '. -_,&' or words[start][1] in specialN):
            name = words[start][0] + name
            start -= 1
        while end < len(words) and (words[end][0] in '. -_,&' or words[end][1] in specialN):
            name += words[end][0]
            end += 1
        return start+1, end, name.strip()
    else:
        while start >= 0 and list(words[start])[1] in specialN:
            start -= 1
        while end < len(words) and list(words[end])[1] in specialN:
            end += 1
        name = ''
        for j in range(start+1, end):
            name += list(words[j])[0]
        return start+1, end, name

# convert Generator to list
def generatorToList(generator):
    # segs, postags, nertags
    """
    return a list of [word, flag] pairs
    """
    words = []
    for word, flag in generator:
        words.append([word, flag])
    return words


# find verbs between 2 (or more) names (people or orgnization)
def findVerb(SEli, nouns, flags, words):
    if len(SEli) < 2:
        return [], [], [], []
    ans = [nouns[0]]
    newFlags = [flags[0]]
    hasVerb = False
    ##
    verbs = []
    names = []
    ##

    for i in range(1, len(SEli)):
        if flags[i] == flags[i-1] or flags[i] == 2:
            continue
        start = SEli[i-1][1]
        end = SEli[i][0]
        for j in range(start, end):
            if words[j][1] == 'v':
                hasVerb = True
                ##
                verbs.append(words[j][0])
                ##
                if newFlags[-1] == 'v':
                    ans[-1] = ans[-1][:-2]+words[j][0]+'>>'
                else:
                    ans.append('<<'+words[j][0]+'>>')
                    newFlags.append('v')
        ##
        names.append(nouns[i])
        ##
        ans.append(nouns[i])
        newFlags.append(flags[i])
    if hasVerb:
        ##
        return ans, newFlags, verbs, names
    else:
        ##
        return [], [], [],[]

# generate dictionary for last names, using 百家姓
def txtToDict(file):
    """
    input:  file path: string
    output: dictionary with all possible last names in Chiness: dictionary
            (length of last names can be 1 or 2)
    """
    with open(file) as f:
        lines = f.readlines()        
        f.close()
    nameDict = defaultdict(bool)
    nameList = []
    for line in lines:
        nameList += line.strip().split(' ')
    
    for name in nameList:
        nameDict[name] = True
        nameDict[name] = True
    return nameDict

# decide if a word is a person's name, using last name dictionary
def isPeople(word, lastNameDict):
    if (lastNameDict[word[:1]] or lastNameDict[word[:2]]) and (1 < len(word) and len(word) < 6):
        return True
    return False

# assign tags to english names, using StanfordNERTagger
def engTagging(word, accurateMode, StanfordTagger):
    """
    return 0 for organization, 1 for people, 2 for others
    """
    tokens = nltk.tokenize.word_tokenize(word)
    if accurateMode:
        tags = StanfordTagger.tag(tokens)
        for tag in tags:
            if tag[1] == 'PERSON':
                return 1
            elif tag[1] in ['ORGANIZATION', 'GPE']:
                return 0
        return 2
    else:
        for chunk in ne_chunk(pos_tag(tokens)):
            if hasattr(chunk, 'label') and chunk.label() == 'PERSON':
                return 1
            elif hasattr(chunk, 'label') and chunk.label() in ['ORGANIZATION', 'GPE']:
                return 0
        return 2

# assaign tags
def tagJudge(word, tag, lastNameDict):
    """
    return 0 for organization, 1 for people, 2 for undefined
    """
    orgTags = ['ns', 'nz', 'nt', 'nl', 'ENG-ORG', 'CONF']
    pplTags = ['nr', 'ENG-PEO']
    undfTags = ['nrt', 'ng', 'nrfg']
    if tag in pplTags:
        return 1
    elif tag in orgTags:
        return 0
    else:
        if isPeople(word, tag, lastNameDict):
            return 1
        return 2
    
# save results to txt files
def saveToTxt(title, listOfContentDict, listOfName, fileName='outputs/test.txt'):
    f = open(fileName,'w+')
    f.write(title + ':\n')
    for contentDict, name in zip(listOfContentDict, listOfName):
        f.write(name + ':\n')
        if type(contentDict) == defaultdict:
            for name, contentList in contentDict.items():
                name = re.sub('[。？！……（）——：；，、]', '', name)
                if name.strip():
                    f.write('\t' + u'\u2022' + name.strip() + '\n')
                    if contentList:
                        contentStr = '+++'.join(contentList)
                        contentStr = re.sub('[\.\-_&。？！……（）——：；，、©]', '', contentStr)
                        contentStr = re.sub(' +', ' ', contentStr)
                        contentStr = re.sub('\+\+\+', ', ', contentStr)
                        if contentStr and contentStr[0] == ',':
                            contentStr = contentStr[2:]
                        f.write('\t' + '\t' + contentStr.strip() + '\n')
        elif type(contentDict) == list or type(contentDict) == set:
            contentDict = list(set(contentDict))
            for item in contentDict:
                item = re.sub('[\.\-_&。？！……（）——：；，、©]', '', item)
                if len(item.strip()) > 1 and 'jiqizhixin' not in item:
                    f.write('\t' + u'\u2022' + item.strip() + '\n')
        f.write('\n\n\n')
    f.close()
    print ('Succesffully saved data to file: ' + fileName + ' !')


def containKeyWords(text, keyWords):
    ans = []
    for word in keyWords:
        if re.findall(word, text, flags=re.M|re.I|re.S):
            ans.append(word.strip())
    return ans

def pruneSentence(sen, pruneKeyWords):
    for keyWord in pruneKeyWords:
        phrases = sen.split(keyWord)
        ans = phrases[0]
        rest = ''
        for word in '。'.join(phrases[1:]):
            if (u'\u4e00' <= word and word <= u'\u9fff') and word not in '：——':
                ans += word
            else:
                rest += word
    return ans, rest


'''# 旧版本，可以返回position
def containKeyWords(sen, keyWords):
    positions = []
    flag = False
    for word in keyWords:
        if re.findall(word, sen, flags=re.M|re.I|re.S):
            flag = True
            it = re.finditer(word, sen, flags=re.M|re.I|re.S)
            for obj in it:
                positions.append([obj.start(0), obj.end(0)])
    
    return flag, positions'''

def findPapersByKeyWords(sen, keyWordsList, mode=[0,0]):
    paperList = []
    # 句中包含“论文”或“paper”的句子
    if containKeyWords(sen, keyWordsList):
        # 如果有冒号，提取冒号之后的部分作为论文名
        sen += '。'
        if re.findall('：', sen, flags=re.M|re.I|re.S):
            paperList.append(re.search('：'+'[^，；。？！……]*?'+'[，；。？！……]', sen, flags=re.M|re.I|re.S).group())
        elif re.findall('——', sen, flags=re.M|re.I|re.S):
            paperList.append(re.search('——'+'[^，；。？！……]*?'+'[，；。？！……]', sen, flags=re.M|re.I|re.S).group())
        else:
            if mode[0]:
                for keyWord in keyWordsList:
                    if re.findall(keyWord, sen, flags=re.M|re.I|re.S):
                        paperList.append(re.search('[，；。？！……]*'+'[^，；。？！……]*?'+keyWord, sen, flags=re.M|re.I|re.S).group())
            if mode[1]:
                for keyWord in keyWordsList:
                    if re.findall(keyWord, sen, flags=re.M|re.I|re.S):
                        paperList.append(re.search(keyWord+'[^，；。？！……]*?'+'[，；。？！……]', sen, flags=re.M|re.I|re.S).group())

    return paperList


def findPapersBySymbel(sen, symbelKeyWords):
    paperList = []
    # 句中包含书名号等特殊字符
    if containKeyWords(sen, [k[0] for k in symbelKeyWords]):
        for symbels in symbelKeyWords:
            if re.findall(symbels[0], sen, flags=re.M|re.I|re.S):
                # 使用greedy匹配找最靠近头、尾的（最长的）匹配结果
                search = re.findall(symbels[0]+'(.*?)'+symbels[1], sen, flags=re.M|re.I|re.S)
                paperList += search
        for paper in paperList:
            sen = re.sub(paper, '', sen, flags=re.M|re.I|re.S)
    return sen,paperList

# 识别长英文
def findPapersByEng(words):
    specialTags = ['m','w','x']
    engTags = ['eng','ENG-ORG','ENG-PEO','CONF']
    paperList = []
    i = 0
    while i < len(words):
        word, flag = words[i]
        if flag in engTags:
            start, end, expandedWord = expandNoun(i, words, specialTags+engTags)
            i = end
            if 'arxiv' in expandedWord.lower():
                continue
            if 'http' in expandedWord.lower():
                continue
            elif expandedWord in paperList:
                continue
            else:
                paperList.append(expandedWord)
        else:
            i += 1
    return paperList


def divideSentence(sen, word):
    if not re.findall(word, sen, flags=re.M|re.I|re.S):
        print ('Word not in sentence.')
        return
    sen = '。' + sen[:] + '。'
    prev = re.search('[，；。？！…… ]'+'[^，；。？！……]*?'+word, sen, flags=re.M|re.I|re.S).group()
    next = re.search(word+'[^，；。？！……]*?'+'[，；。？！…… ]', sen, flags=re.M|re.I|re.S).group()
    
    prevDeleteEmptyLine = re.sub('[，；。？！…… ]', '', prev)
    nextDeleteEmptyLine = re.sub('[，；。？！…… ]', '', next)
    return prevDeleteEmptyLine[:-len(word)].strip(), nextDeleteEmptyLine[len(word):].strip()


def findOrg(words, specialN, useExpanded, lastNameDict, accurateMode, StanfordTagger):
    orgList = []
    i = 0
    while i < len(words):
        word, flag = words[i]
        if flag in specialN+['eng']:
            if flag == 'eng':
                start, end, expandedWord = expandNoun(i, words, specialN)
                tag = engTagging(expandedWord, accurateMode, StanfordTagger)
            else:
                tag = tagJudge(word, flag, lastNameDict)
            if useExpanded[tag] and flag != 'eng':
                start, end, expandedWord = expandNoun(i, words, specialN+['n'])
            elif flag != 'eng':
                start, end = i, i+1
                expandedWord = word

            if tag == 0:
                orgList.append(expandedWord)

            i = end
        else:
            i += 1
    return orgList


def findNumber(words):
    numberList = []
    i = 0
    while i < len(words):
        word, flag = words[i]
        if flag == 'm':
            start, end, expandedWord = expandNoun(i, words, ['m','x'])
            i = end
            numberList.append(expandedWord)
        else:
            i += 1
    return numberList


def createDict(f):
    file = open(f, 'r') 
    lines = file.readlines()
    customList = []
    for line in lines:
        if line not in customList:
            customList.append(line.lower().strip())
    return customList


def pairTitle(PEOList, TTLList, ORGList, words, titleDict, currTimeString):
    pairDict = defaultdict(list)
    for intT, t in TTLList:
        minDist, minP = sys.maxsize, ''
        for intP, p in PEOList:
            if intT[0] < intP[0]:
                if abs(intP[0] - intT[1]) < minDist:
                    minDist = abs(intP[0] - intT[1])
                    minP = p
            else:
                if abs(intT[0] - intP[1]) < minDist:
                    minDist = abs(intT[0] - intP[1])
                    minP = p
        if not pairDict[minP.strip()]:
            pairDict[minP.strip()] = [[], []]
        pairDict[minP.strip()][0].append(str(t.strip()))

    for intO, o in ORGList:
        minDist, minP = sys.maxsize, ''
        for intP, p in PEOList:
            if intO[0] < intP[0]:
                if abs(intP[0] - intO[1]) < minDist:
                    minDist = abs(intP[0] - intO[1])
                    minP = p
            else:
                if abs(intO[0] - intP[1]) < minDist:
                    minDist = abs(intO[0] - intP[1])
                    minP = p
        if (not pairDict[minP.strip()]) or (not pairDict[minP.strip()][0]) or (o.strip() in pairDict[minP.strip()][1]):
            continue
        pairDict[minP.strip()][1].append(str(o.strip()))

    for people, contentList in pairDict.items():
        if people and contentList and contentList[0]:
            orgString = ', 机构: '+', '.join(contentList[1]) if contentList[1] else ''
            titleDict[people].append('职位: '+', '.join(contentList[0])+orgString+currTimeString)
    return titleDict


def trimTitle(titleDict):
    for people, titleList in titleDict.items():
        titles = list(set(titleList))
        titles = sorted(titles, key=lambda k:len(k))
        i = 0
        while i < len(titles):
            j = i+1
            while j < len(titles):
                short = titles[i]
                long = titles[j]
                if short.strip() in long.strip():
                    titles.remove(short)
                    j = i+1
                else:
                    j += 1
            i += 1
        if titles:
            titleDict[people] = titles
    return titleDict

def getRound(sen):
    roundSet = set([])
    if containKeyWords((sen), ['轮']):
        roundList = re.findall('[A-Za-z0-9-\+\- ]+' + '轮', (sen), flags=re.M | re.I | re.S)
        for round in roundList:
            roundSet.add((re.sub('[ \.\-_&。？！……（）——：；，、©]', '', round)).strip())
    return list(roundSet)

def findFinancialRelation(words, financialDict, currRoundString, currMoneyString, currTimeString):
    if all([w[1]=='x' for w in words]):
        return
    org = ''
    verb = ''
    for word, tag in words:
        if word in ['，', '；', '：']:
            if org and verb:
                if (org+' ('+verb+') ').strip() not in financialDict:
                    financialDict[(org+' ('+verb+') ').strip()].append(currRoundString + currMoneyString + currTimeString)
            org, verb = '', ''
        elif tag == 'ORG':

            if not verb:
                org = word
            else:
                if (org+' ('+verb+') '+word).strip() not in financialDict:
                    print ((org+' ('+verb+') '+word).strip())
                    financialDict[(org+' ('+verb+') '+word).strip()].append(currRoundString + currMoneyString + currTimeString)
                org, verb = '', ''
        elif tag == 'FNC':
            if org and (not verb):
                verb = word
            elif org and verb:
                if (org+' ('+verb+')').strip() not in financialDict:
                    financialDict[(org+' ('+verb+')').strip()].append(currRoundString + currMoneyString + currTimeString)
                org, verb = '', ''
        else:
            continue

    return



'''
def findAuthors(words, accurateMode, StanfordTagger, useExpanded, lastNameDict, specialN):
    authorList = []
    i = 0
    while i < len(words):
        word, flag = words[i]
        if flag in ['nr','eng','nrt','ng','nrfg','ENG-PEO']:
            if flag == 'eng':
                start, end, expandedWord = expandNoun(i, words, specialN)
                tag = engTagging(expandedWord, accurateMode, StanfordTagger)
            else:
                tag = tagJudge(word, flag, lastNameDict)
            
            if useExpanded[tag] and flag != 'eng':
                start, end, expandedWord = expandNoun(i, words, specialN)
            elif flag != 'eng':
                start, end = i, i+1
                expandedWord = word

            if tag == 1 and expandedWord not in authorList:
                authorList.append(expandedWord)

            i = end
        else:
            i += 1
    return authorList


def findAbbr(words):
    abbrList = []
    i = 0
    while i < len(words):
        word, flag = words[i]
        if flag in ['eng','ENG-PEO','ENG-ORG','CONF']:
            start, end, expandedWord = expandNoun(i, words, ['m','x','eng','ENG-PEO','ENG-ORG','CONF'])
            i = end
            if len(expandedWord.strip().split(' ')) < 4:
                abbrList.append(expandedWord.strip())
        else:
            i += 1
    return abbrList

'''