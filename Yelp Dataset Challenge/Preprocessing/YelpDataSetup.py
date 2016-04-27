import re
import json
import ast
import nltk
from Parser import *
from Preprocess import *
from nltk.stem.porter import PorterStemmer
from nltk.metrics import edit_distance
from nltk.tokenize import wordpunct_tokenize
from xlrd import open_workbook

BUSINESS_PATH = "../../../YelpData/small_business.json"
REVIEW_PATH = "../../../YelpData/small_review.json"
OUTPUT_TEST_PATH = "../../../YelpData/testAnswers.json"
OUTPUT_CATEGORY_PATH = "../../../YelpData/category.json"

bdoc = open(BUSINESS_PATH)
rdoc = open(REVIEW_PATH)
excel_doc = open_workbook('../../../YelpData/yelp-business-categories-list.xlsx').sheet_by_index(0)

obdoc = open(OUTPUT_TEST_PATH, "w+")
ocdoc = open(OUTPUT_CATEGORY_PATH, "w+")

#Parse business document with reviews
trainDict = {}  #Training business dictionary
testDict = {} #Testing business dicitonary

# contains only the 47 main business categories
main_category_list = []

# extract the main business categories from first column of Excel file and insert to list
cat_count = 0;
for rownum in range(3, excel_doc.nrows):
    cat = str(excel_doc.cell(rownum, 0).value)
    if cat != '':
        main_category_list.append(cat)
        cat_count += 1
# print main_category_list

bdoc_str = ""
for line in bdoc:
    entry = line.strip('\n')
    json_obj = json.loads(entry)
    for cat in list(json_obj['categories']):
        index = json_obj['categories'].index(str(cat))
        if json_obj['categories'][index] not in main_category_list:
            del json_obj['categories'][index]
    entry = json.dumps(json_obj)
    # append modified entry into bdoc_str
    bdoc_str += str(entry)
    bdoc_str += "\n"

bdoc.close()

bdoc = open(BUSINESS_PATH, "wb+")
# write entire new json object into small_business.json file
bdoc.write(bdoc_str)

bdoc.close()

#Training/Testing partition
size =  len(rdoc.readlines())
rdoc.seek(0,0)
trainSize = size*(.9)
currSize = 0

porter_stemmer = PorterStemmer()

for line in rdoc:
# Size counts for paritioning training and testing
    currSize += 1
    b = json.loads(line)
    bkey = b['business_id']
    review = b['text']
    attributes = b['attributes']
    # tokenize the sentence by white space and punctuations; prepare for stemming
    new_sent = wordpunct_tokenize(review)

    new_review = ''
    # stem each words in the sentence
    for w in new_sent:
        # remove recurring punctuations and special punctuations
        w = removeExtraPunc(w)
        # decapitalize each word
        w = w.lower()
        # remove pronouns
        w = removePronouns(w, True)
        # remove preposition
        w = removePrepositions(w)

        w = removeBe(w)
        w = removeConjunction(w)

        w = removeNumbers(w)

        # remove apostrophe & postfix of Apostrophe
        w = removeApostrophe(w, True)
        w = removePostfixApos(w, True)

        # Stemming
        new_review += porter_stemmer.stem(w)
        new_review += " "

    # remove extra spaces
    new_review = removeMultipleSpaces(new_review)
    # print "ORI: " + review + "\n"
    # print "NEW: " + new_review + "\n"

    if currSize <= trainSize:

        if bkey not in trainDict:
            Bus = BusinessParser(bkey)
            trainDict[bkey] = Bus

        trainDict[bkey].addText(new_review)
    else:
        if bkey not in testDict:
            Bus = BusinessParser(bkey)
            testDict[bkey] = Bus

        testDict[bkey].addText(new_review)
        testDict[bkey].addRawAttribute(attributes)
        #Grab raw json for attributes

bdoc = open(BUSINESS_PATH)
#Parse categories with businesses
bdoc.seek(0,0)
cdict = {}
for line in bdoc:
    b = json.loads(line)
    bkey = b['business_id']
    categories = b['categories']
    if bkey in trainDict:
        bobj = trainDict[bkey]
        words = bobj.dictionary
        numWords = bobj.numWords
        for category in categories:
            if category not in cdict:
                Cat = CategoryParser(category)
                cdict[category] = Cat

            cdict[category].addBusiness(bkey)
            cdict[category].updateReview(words,numWords)

    elif bkey in testDict:
        testDict[bkey].addCategory(categories)
        # print(testDict[bkey].toJSONMachine())

#Overwrite all previous file data
# obdoc.seek(0,0)
# for bkey in bdict:
#     obdoc.write(bdict[bkey].toJSONMachine()+'\n')
obdoc.seek(0,0)
for bkey in testDict:
    obdoc.write(testDict[bkey].toJSONMachine()+'\n')
ocdoc.seek(0,0)
for ckey in cdict:
    ocdoc.write(cdict[ckey].toJSONMachine()+'\n')

bdoc.close()
