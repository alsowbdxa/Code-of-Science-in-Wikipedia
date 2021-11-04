#######################################################
#extract dimension data
import time
import requests
import multiprocessing
from multiprocessing import Pool
from bs4 import BeautifulSoup
import json
import random
from tqdm import tqdm

doi = []
for line in open('read the doi files you need',"r",encoding='utf8'): 
    doi.append(line.strip())

def get_access():
    #   The credentials to be used
    KEY = # your private API key
    ENDPOINT = 'app.dimensions.ai'  # the Dimensions server you are using

    login = {
        'key': KEY
    }
    #   Send credentials to login url to retrieve token. Raise
    #   an error, if the return code indicates a problem.
    #   Please use the URL of the system you'd like to access the API
    #   in the example below.
    resp = requests.post(f'https://{ENDPOINT}/api/auth.json', json=login)
    resp.raise_for_status()

    #   Create http header using the generated token.
    headers = {
        'Authorization': "JWT " + resp.json()['token']
        ,'User-Agent': random.choice(ua)
    }
    return headers


def job(url, header1):
    run = 1
    while run<4:
        try:
            r = session.post(
                'https://app.dimensions.ai/api/dsl.json',
                data=url,
                headers=header1,proxies=get_proxy())
        except:
            r = requests.post(
                'https://app.dimensions.ai/api/dsl.json',
                data=url,
                headers=header1)
        if 'total_count' not in r.text:
            time.sleep(random.randint(1,3))
            run+=1
        else:
            content.append(r.text)
            qc.append(url)
            time.sleep(1)
            break
    if run == 4:
        lack.append(url)
        print(len(lack))

ua = [
      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
  		'Opera/8.0 (Windows NT 5.1; U; en)',
  		'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
  		'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
  		'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2 ',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
  		'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
  		'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
  		'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
  		'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
  		'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
  		'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0) ',
      ]
lack=[]
qc = []

query_template_1 = 'search publications where %s in ["'
query_template_2 = '"] return publications[basics+publisher+category_for+mesh_terms+concepts_scores+date+doi+open_access_categories_v2+authors+authors_count+relative_citation_ratio+research_org_countries+recent_citations+field_citation_ratio+times_cited] limit 300'

urls=[]
for i in range(0,len(doi),300):
    try:
        b = doi[i:i+300] 
    except:
        b = doi[i:]
    urls.append(b)

content=[]
session = requests.session()
header1 = get_access()

for i in tqdm(urls):
    url = (query_template_1%'doi'+'","'.join(i)+query_template_2).encode()
    url = url.replace('\\n'.encode(),''.encode())
    url = url.replace('\t'.encode(),''.encode())
    url = url.replace('\\t'.encode(),''.encode())
    url = url.replace('\\'.encode(),''.encode())
    url = url.replace('t\\'.encode(),''.encode())
    if url in qc:
        continue
    if url in lack:
        continue
    job(url,header1)
############################## Extracting data from Dimensions End ##########################################

#Extract the data from the result above
fields = []
dois= []
journal = []
open_access = [] #open_access_categories_v2
recent_citations = [] 
research_org_countries = []
times_cited = [] 
types =[]
year = []

doi = []
for line in open("above file's name","r",encoding='utf8'): 
    doi.append(line.strip())


for i in tqdm(doi):
    c = json.loads(i)['publications']
    for n in c:
        try:
            fields.append(n['category_for'])
        except:
            fields.append('')
        try:
            dois.append(n['doi'])
        except:
            dois.append('')
        try:
            journal.append(n['journal']['title'])
        except:
            journal.append('')
        try:
            open_access.append(n['open_access_categories_v2'][0])
        except:
            open_access.append('')
        try:
            recent_citations.append(n['recent_citations'])
        except:
            recent_citations.append('')
        try:
            research_org_countries.append(n['research_org_countries'])
        except:
            research_org_countries.append('')
        try:
            times_cited.append(n['times_cited'])
        except:
            times_cited.append('')
        try:
            types.append(n['type'])
        except:
            types.append('')
        try:
            year.append(n['year'])
        except:
            year.append('')
