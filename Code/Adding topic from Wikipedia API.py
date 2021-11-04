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
qc = []
for line in open(file of finished wiki article titles,"r",encoding='utf8'): 
    qc.append(line.strip())
    
for i in tqdm(l1):
    if i in qc:
        continue
    link = 'https://wikipedia-topic.wmcloud.org/api/v1/topic?threshold=0.15&lang=en&title='
    # page_title = 'Chow group'
    url = link+i
    # header={
    #             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
    #             ,'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    #             ,'accept-encoding': 'gzip, deflate, br'
    #             ,'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6'   
    #         }   
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
