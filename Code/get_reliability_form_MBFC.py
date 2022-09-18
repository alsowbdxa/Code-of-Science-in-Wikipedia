##############################################################################
## get reliability fact check
##
import pandas as pd
import requests as r
from tqdm import tqdm
from bs4 import BeautifulSoup

results = []
qc = []
error = [] # only save title
error1 = [] #save title and response
leaning = [
    'https://mediabiasfactcheck.com/center/',
    'https://mediabiasfactcheck.com/left/',
    'https://mediabiasfactcheck.com/leftcenter/',
    'https://mediabiasfactcheck.com/right-center/',
    'https://mediabiasfactcheck.com/right/',
    'https://mediabiasfactcheck.com/conspiracy/',
    'https://mediabiasfactcheck.com/fake-news/',
    'https://mediabiasfactcheck.com/pro-science/',
    'https://mediabiasfactcheck.com/satire/'
]

for index in tqdm(range(len(leaning))):
    resp = r.get(leaning[index])
    print('Getting resources: {}'.format(leaning[index]))
    soup = BeautifulSoup(resp.text, 'html.parser')

    table = soup.find('table', id='mbfc-table')
    rows = table.find_all('tr')

    for r_index in tqdm(range(len(rows))):
        try:
            title = rows[r_index].find('a').text
        except:
            continue
        if title in qc:
            continue
        if title in error:
            continue
        source_url = rows[r_index].find('a')['href']
        source_resp = r.get(source_url)
        
        try:
            url = title.split('(')[1].split(')')[0]  
            if '.' not in url:
                e = 1/0
        except:
            try:
                s = BeautifulSoup(source_resp.text.split('Source:')[1], 'html.parser')
                url = s.find('a').text 
            except:
                try:
                    url = 'https://www.{}.com/'.format(source_url.split('com')[1].replace('/','').replace('-',''))
                except:
                    url = 'Not Found'
                          
        try:
            s_resp = source_resp.text.split('>Detailed Report')[1]
        except:
            try:
                s_resp = source_resp.text.split('>Detailed Record')[1]
            except:
                error.append(title)
                error1.append([title,source_resp])
                continue
        # soup_source = BeautifulSoup(source_resp.text, 'html.parser')
        # bias_rating = leaning[index].split('com')[-1].replace('/','')
        # bias_rating = url = factual_status = MBFC_Credibility_Rating = country =  ''

        soup_info = BeautifulSoup(s_resp, 'html.parser')
        info = soup_info.findAll('p')[0].text
        cate = leaning[index].split('com')[-1].replace('/','')
        try:
            bias_rating = info.split('Bias Rating:')[1].split('\n')[0].strip()
        except:
            bias_rating = 'Not Found'
        
        try:
            MBFC_Credibility_Rating = info.split('MBFC Credibility Rating:')[1].split('\n')[0].strip()
            # MBFC_Credibility_Rating = source_resp.text.split('MBFC Credibility Rating:')[1].split('strong')[1]
            # MBFC_Credibility_Rating = MBFC_Credibility_Rating.replace('>','').replace('<','').replace('/','')
        except:
            MBFC_Credibility_Rating = 'Not Found'
        
        try:
            country = info.split('Country:')[1].split('\n')[0].strip()
            # country = source_resp.text.split('Country:')[1].split('<')[1].split('>')[-1].split("(")[0].strip()
        except:
            country = 'Not Found'
            
        try:
            factual_status = info.split('Factual Reporting:')[1].split('\n')[0].strip()
            # factual_status = source_resp.text.split('Factual Reporting:')[1].split('-')[0].strip()
        except:
            try:
                factual_status = source_resp.text.split('Factual Reporting:')[1].split('-')[0].strip()
            except:
                factual_status = 'Not Found'
            
        try:
            traffic = info.split('Traffic/Popularity:')[1].split('\n')[0].strip()
        except:
            traffic = 'Not Found'
            
        try:
            Press_Freedom_Rating = info.split('Press Freedom Rating:')[1].split('\n')[0].strip()
        except:
            try:
                Press_Freedom_Rating = info.split('World Press Freedom Rank:')[1].split('\n')[0].strip()
            except:
                Press_Freedom_Rating = 'Not Found'
            
        results.append([title, cate, url, bias_rating, factual_status, country, MBFC_Credibility_Rating,traffic,Press_Freedom_Rating])
        qc.append(title)

df = pd.DataFrame(results, columns=['Title', 'cate', 'URL', 'bias_rating', 'Factual Label', 'Country', 'MBFC_Credibility_Rating', 'Traffic/Popularity', 'Press_Freedom_Rating'])
df.to_excel('mbfc.xlsx', index=False, encoding='utf-8-sig')
