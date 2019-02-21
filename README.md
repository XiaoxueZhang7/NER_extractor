# Named Entity Recognition
# 命名体识别

这个脚本用于识别机器之心官网上不同类型文章中出现的名命题和关系信息。


## Getting Started


### Prerequisites

#### [ChromeDriver](https://github.com/SeleniumHQ/selenium/wiki/ChromeDriver)

ChromeDriver is a separate executable that WebDriver uses to control Chrome. It is maintained by the Chromium team with help from WebDriver contributors. If you are unfamiliar with WebDriver, you should check out their own Getting Started page.



#### [Java JRE 8 or higher](https://blog.sicara.com/train-ner-model-with-nltk-stanford-tagger-english-french-german-6d90573a9486)

Because Stanford NER tagger is written in Java, you are going to need a proper Java Virtual Machine to be installed on your computer.

To do so, install Java JRE 8 or higher. You can install Java JDK (developer kit) if you want because it contains JRE. For Linux users, you will find all needed information on this guide on How To Install Java with Apt-Get on Ubuntu 16.04. For other users, please have a look at Java official documentation.


#### [NLTK models]
Use NLTK Downloader to download the models: 
```
import nltk
nltk.download('punkt')
nltk.download('maxent_treebank_pos_tagger')
```
### Documents


#### Stanford Named Entity Recognizer (NER): [https://nlp.stanford.edu/software/CRF-NER.shtml](https://nlp.stanford.edu/software/CRF-NER.shtml)

* 需要的文件已在```docs```路径下：[stanford-ner-2014-08-27](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/docs/stanford-ner-2014-08-27) 


#### 百家姓文件

* 需要的文件已在```docs```路径下：[last name.txt](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/docs/last%20name.txt) 

#### 本地词典文件

* 需要的文件已在```docs```路径下：[combined-people.txt](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/docs/combined-people.txt)  ，[combined-organization.txt](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/docs/combined-organization.txt) ，[combined-conference.txt](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/docs/combined-conference.txt) 。


## Deployment
针对三种不同的识别任务，[scripts](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/scripts)文件夹下分别对应三个文件
：

* [NER_AO](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/scripts/NER_AO.py)：识别文章中的人物、机构信息，及之间的关系。
* [NER_PA](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/scripts/NER_PA.py)：识别文章中的会论文、作者、会议信息。
* [NER_OO](https://github.com/chainn/synced_datalab/edit/master/Xiaoxue/NER/scripts/NER_OO.py)：识别文章中的投融资、合作关系。



### Parameters：

* articleType：必填，```string```；
* articleUrl：对于给定url识别文章的情况必填，对于自动识别AIDaily类型的多篇文章可缺省， ```sting```；
* autoCrawlAI：对于自动识别AIDaily类型的多篇文章必填为```True```，其他情况可缺省；
* articleNumberAI：对于自动识别AIDaily类型的多篇文章可选填需要提取的文章数量，```int```，默认为10篇，其他情况可缺省；
* contentMode：(仅对NER_AO)是否使用```[标题，文章内容，短描述]```进行分析，```1```表示使用，```0```表示不使用，默认为```[1,1,0]```，即使用标题和文章内容，不使用短描述；
* paperMode：(仅对NER_PA)是否通过```[关键词, 特殊字符, 长英文]```提取文章，```1```表示使用，```0```表示不使用，默认为```[1,1,1]```，即三种方法均使用；
* orgMode：(仅对NER_OO)是否对动词```[前, 后, _]```的部分进行机构名提取，```1```表示提取，```0```表示不提取，默认为```[0,0,0]```，即直接输出结果，不进行机构名提取；
* useExpanded：是否对```[机构名, 人名, 其他名词]```进行前后扩展，```1```表示扩展，```0```表示不扩展，默认为```[0,0,1]```，即三种方法均使用；
* accurateMode：是否使用```StanfordNERTagger```对英文进行词性标注，```True```表示使用```StanfordNERTagger```(速度较慢，准确度较高)，```False```表示使用```nltk.ne_chunk```，默认为```False```
* dirName：输出文档的储存路径，默认在当前目录下新建一个```outputs```文件夹储存输出的txt文件，文件名为对应的文章标题名。

## Author

**Xiaoxue Zhang** 
