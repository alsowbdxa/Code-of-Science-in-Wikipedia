import os
import nltk
import numpy as np
import pandas as pd
import networkx as nx
import seaborn as sns
from tqdm import tqdm
from collections import Counter
import matplotlib.pyplot as plt
from itertools import *
import bisect
import leidenalg as la
import gc
import igraph as ig

tqdm.pandas()
sns.set(style="darkgrid")

#############
# Input WikipediaCitations minimal
# Read WikipediaCitations minimal 
# start

INPUT_DATA = 'minimal_dataset.parquet' #can be found from : https://github.com/Harshdeep1996/cite-classifications-wiki
# read the data
citations = pd.read_parquet(INPUT_DATA)#size is 29276667

def clean(i):
   if i==None:
       return None
   if 'DOI' in i:
       doi_string = i[i.find('DOI')+4:]
       cm = doi_string.find(',')
       pr = doi_string.find('}')
       cut = cm
       if cut < 0 or (pr > 0 and cut > pr):
           cut = pr
       d = doi_string[:cut].lower()
       if len(d)>0:
           doi = d
       else:
           doi = None
   else:
       doi = None
   return doi

def clean1(i):
   if '[' in str(i):
       doi = i[0].lower()
   else:
       doi = None
   return doi
   
citations['article_id'] = citations['ID_list'].progress_apply(lambda x:clean(x))
citations['ndoi'] = citations['updated_identifier'].progress_apply(lambda x:clean1(x))
citations['doi']=citations['article_id'].combine_first(citations['ndoi'])

result = citations[['page_title','doi']]

result1 = result.dropna(subset = ['doi'])# size is 1705085

# Input WikipediaCitations minimal
# Read WikipediaCitations minimal 
# end
#############
