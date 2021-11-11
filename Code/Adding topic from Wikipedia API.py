import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import xlrd
import re
import math
import time
import random
import json
from tqdm import tqdm
import urllib.parse

#################  Supplementary article topics via wikipedia api  ########################
l2=[[],[]]
session = requests.session()
l1 = []
for line in open(file of needed wiki article titles,"r",encoding='utf8'): 
    l1.append(line.strip())
#here the l1 could use all the unique wikipedia page title which is included in the documents "page_doi.parquet" in the file "Input and read the dataset.py" 
# l1 = pd.read_parquet('\page_doi.parquet')
# l1 = list(set(l1['page_title'].to_list()))

qc = [] # this step is just to avoid repeat requests once stoped when the code is running
for line in open('qc.txt',"r",encoding='utf8'): #file of finished wiki article titles
    qc.append(line.strip())
    
for i in tqdm(l1):
    if i in qc:
        continue
    link = 'https://wikipedia-topic.wmcloud.org/api/v1/topic?threshold=0.15&lang=en&title=' # More information in the website https://wiki-topic.toolforge.org//topic
    # page_title = 'Chow group' # example
    url = link+i
    header={
                'User-Agent': random.choice(ua)
                ,'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
                ,'accept-encoding': 'gzip, deflate, br'
                ,'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'   
            }   
    while 1:
        try:
            data = session.get(url,headers=header,timeout=30).content.decode('gbk') 
            if 'article' in data:
                break
            else:
                time.sleep(random.randint(3,5))
        except:
            time.sleep(random.randint(3,5))
    try:
        topic = json.loads(data)['results']
    except:
        topic = ''
    l2[0].append(i)
    l2[1].append(str(topic))
    qc.append(i)
    
with open(r"qc.txt", 'a',encoding='utf-8') as f:
    for i in qc:
        f.write(i+'\n')
        
frames1 = [pd.DataFrame(i) for i in l2]
result3 = pd.concat(frames1,axis=1)
result3.to_parquet(r'page_topic.parquet',encoding='utf_8_sig')

    
