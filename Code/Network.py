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

#read and clean the data with doi

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

########## create co-citation network matrix start #########################
#co-citation network
g1 = result1.groupby('page_title')
g2=[i[1]['doi'] for i in g1] # the size of g2 is 405358
g3 = [i for i in g2 if len(i)>1] #the size of g3 is 201987

node_list = list(set([x for i in g3 for x in i])) # size:1050686; generate a node list of cited artical
node_list.sort() #prepare for the next step: bisect_left need an order list
edge_list = []#size is 17816861

for i in tqdm(g3):  #it costs 9 seconds to get the edge_list
    p = [x for x in i] #list of cited artical doi in each wiki page
    c=sorted([bisect.bisect_left(node_list, x) for x in p]) #index of each doi in the whole list(node_list)
    edge_list.append(list(combinations(c,2))) #generat edge_list for each wiki page by combinations(from itertools import *)

dic={}#edge number is 17916861, and key is edge, value is weight of the edge
for x in tqdm(edge_list):#19 seconds
    for y in x:
        try:
            dic[y]+=1
        except:
            dic[y] = 1
key = list(dic.keys())
value = list(dic.values())

g=ig.Graph()
g.add_vertices(len(node_list))
g.add_edges(key[:])
g.es[:]['weight']=value[:]
g.vs['weight']=[1 for i in range(len(node_list))]
g.vs['name'] = node_list

#use leiden detect the community
cluster_solution = g.community_leiden(resolution_parameter=0.0001, n_iterations=2,weights=g.es['weight'],node_weights=g.vs['weight'])
# to draw the network of clusters
super_graph = cluster_solution.cluster_graph(combine_vertices={'weight': 'sum'},combine_edges={'weight': 'sum'})

to_delete_ids = [v.index for v in s1.vs if v.degree() == 0]
super_graph.delete_vertices(to_delete_ids)# co-citation node:31515
ig.write(super_graph,file_name,format='gml') #use this file in Gephi and draw the co-citation network plot
############# co-citation network end #######################################

############### figure 1 start #####################
# to draw the relationship between the resolution and the number of clusters
n=[0.1**i for i in range(1,12)]
cluster_num=[]
for i in tqdm(n):
    cluster_solution = g.community_leiden(resolution_parameter=i, n_iterations=2,weights=g.es['weight'],node_weights=g.vs['weight'])
    cluster_num.append(len(cluster_solution))
    
plt.plot(n,cluster_num)
plt.xlabel('resolution parameter')
plt.ylabel('number of clusters')
############### figure 1 end #####################

######## Bibliographic coupling network start ################
g11 = result.groupby('doi')
g22=[i[1]['page_title'] for i in g11] # the size of g2 is 1157571
g33 = [i for i in g22 if len(i)>1] #the size of g3 is 231129

node_list = list(set([x for i in g33 for x in i])) # size:257452; generate a node list of cited artical
node_list.sort() #prepare for the next step: bisect_left need an order list
edge_list = []#size is 27473262

for i in tqdm(g33):  #it costs 7 seconds to get the edge_list
    p = [x for x in i] #list of cited artical doi in each wiki page
    c=sorted([bisect.bisect_left(node_list, x) for x in p]) #index of each doi in the whole list(node_list)
    edge_list.append(list(combinations(c,2))) #generat edge_list for each wiki page by combinations(from itertools import *)

dic={}#edge number is 27473262, and key is edge, value is weight of the edge
for x in tqdm(edge_list):#30 seconds
    for y in x:
        try:
            dic[y]+=1
        except:
            dic[y] = 1
key = list(dic.keys())
value = list(dic.values())

g=ig.Graph()
g.add_vertices(len(node_list))
g.add_edges(key[:])
g.es[:]['weight']=value[:]
g.vs['weight']=[1 for i in range(len(node_list))]
g.vs['name'] = node_list

# g.density()
# Out[13]: 0.0008289901502753311

#use leiden detect the community
cluster_solution = g.community_leiden(resolution_parameter=0.0001, n_iterations=2,weights=g.es['weight'],node_weights=g.vs['weight'])

sb = pb.cluster_graph(combine_vertices={'weight': 'sum'},combine_edges={'weight': 'sum'})

sb.vcount()

tb = [v.index for v in sb.vs if v.degree() == 0]
sb.delete_vertices(tb)

ig.write(sb,file_name,format='gml') #use this file in Gephi and draw the bibliographic coupling network plot

testread = ig.read(file_name,format='gml')

########## Bibliographic coupling network end ####################

############# analysis Bibliographic coupling network start #############
#g.vount()#  the number of nodes
#g.ecount() # the number of edges
#g.vs[] #each node's information
#g.es[] #each edge's information
g.vs['label']=node_list
degree = g.degree()
neighbors = dict(zip(g.vs['label'], degree))
neighbors_sorted = sorted(neighbors.items(), key=lambda e: e[1],reverse=True)

betweenness = g.betweenness()
betweenness = [round(i, 1) for i in betweenness]
node_betweenness = dict(zip(g.vs['label'], betweenness))
node_betweenness_sorted = sorted(node_betweenness.items(), key=lambda e: e[1],reverse=True)

partition.total_weight_in_all_comms() #result=12760
#get all the subgraphs
subgraphs=partition.subgraphs()#type is list, and size is 1240
################### analysis Bibliographic coupling network end ####################

# add fields to co-citation network
field = [doi2fields[i] for i in g.vs['name']]
g.vs['field'] = field

cluster_solution = g.community_leiden(resolution_parameter=0.0001, n_iterations=2,weights=g.es['weight'],node_weights=g.vs['weight'])
super_graph = cluster_solution.cluster_graph(combine_vertices={'weight': 'sum'},combine_edges={'weight': 'sum'})

t2=[]
t3=[]
for i in tqdm(cluster_solution):
    f = [g.vs[n]['field'] for n in i]
    f=sorted(f)
    c = Counter(f)
    t2.append(c.most_common(1)[0][0])

super_graph.vs['field'] = t2

t1=super_graph.vs['weight']
t1=sorted(t1,reverse=1)#from large to small

# sum(t1[:475])/sum(t1)
# Out[435]: 0.7001302006498611

# t1[475]
# Out[436]: 137.0

tb = [v.index for v in super_graph.vs if v['weight'] < 137] #to filter more than 70%
super_graph.delete_vertices(tb)

ig.write(super_graph,file_name,format='graphml')
##############################################
# add topic and wk_project to biblio network
topic = [page2topics[i] for i in gb.vs['name']]
wk = [page2wk_projects[i] for i in gb.vs['name']]

gb.vs['topic'] = topic
gb.vs['wk_project'] = wk

cb = gb.community_leiden(resolution_parameter=0.0001, n_iterations=2,weights=gb.es['weight'],node_weights=gb.vs['weight'])
sb = cb.cluster_graph(combine_vertices={'weight': 'sum'},combine_edges={'weight': 'sum'})

t2=[]
t3=[]
for i in tqdm(cb):
    f = [gb.vs[n]['topic'] for n in i]
    f=sorted(f)
    c = Counter(f)
    t2.append(c.most_common(1)[0][0])

for i in tqdm(cb):
    f = [gb.vs[n]['wk_project'] for n in i]
    f=sorted(f)
    c = Counter(f)
    t3.append(c.most_common(1)[0][0])

sb.vs['topic'] = t2
sb.vs['wk'] = t3

t1=sb.vs['weight']
t1=sorted(t1,reverse=1)#from large to small

# t1[232]
# Out[485]: 44.0

# sum(t1[:232])/sum(t1)
# Out[486]: 0.7009695011108867

tb = [v.index for v in sb.vs if v['weight'] < 45] #to filter more than 70%
sb.delete_vertices(tb)

ig.write(sb,file_name,format='graphml') #
################################################################

########### river plot ####################################3
d1 = pd.read_parquet(file with wikipedia projects and topics)
dic = dict(zip(test['doi'],test['fields']))
tqdm.pandas()
d1['fields'] = d1['doi'].progress_apply(lambda x:dic[x])

t1=d1[['new_topic','fields']]
t1=t1.dropna(subset=['new_topic'])#1705084
t1=t1.dropna(subset=['fields'])  #1629836
t2 = t1['new_topic'].to_list()
t5 = []
for i in tqdm(t2):
    if len(i)>2:# have'','[]'
        t5.extend(eval(i)[0])
t5=list(set(t5)) #63

t2 = t1['fields'].to_list()
t6 = []
for i in tqdm(t2):
    if len(i)>2:# 
        c = eval(i)
        a = [i['name'] for i in c]
        t6.extend(a)
t6=list(set(t6)) #175

t3 = t1['new_topic'].to_list()
t4 = t1['fields'].to_list()
t5.sort()
t6.sort()
a=[i.split('.')[0] for i in t5]
t8=list(set(a))
t7=[x+'+'+y[:2] for x in t8 for y in macro]

dic = dict(zip(t7,[0 for i in range(len(t7))]))
for i in tqdm(range(len(t3))):
    if len(t3[i])>2:
        if len(t4[i])>2:
            a = [i.split('.')[0] for i in eval(t3[i])[0]]
            c = [i[:2] for i in [n['name'] for n in eval(t4[i])]]
            unique_field = list(set(c))            
            for x in a:
                for y in unique_field:
                    dic[x+'+'+y]+=float(c.count(y))/float(len(c))
        
######################## topic to macro fields #####################

#river plot of wk project and macro fields
dic = dict(zip(data['doi'],data['wk+topics']))
d1['wk_project'] = d1['doi'].progress_apply(lambda x:dic[x])
def clean(x):
    try:
        return dic[x]['wk_project']
    except:
        return ''
d1['wk_project'] = d1['doi'].progress_apply(lambda x:clean(x))
t1=d1[['wk_project','fields']]
t1=t1.dropna(subset=['wk_project'])#1705085
t1=t1.dropna(subset=['fields'])  #1629837
t2 = t1['wk_project'].to_list()
t3=[]
for i in tqdm(t2):
    for a in i:
        if a not in t3:
            t3.append(a)  #57684
t3.sort()
t7=[x+'+'+y[:2] for x in t3 for y in macro]

t3 = t1['wk_project'].to_list()
t4 = t1['fields'].to_list()

dic = dict(zip(t7,[0 for i in range(len(t7))]))
for i in tqdm(range(len(t3))):
    if type(t3[i])==list:
        if len(t4[i])>2:
            a = t3[i]
            c = [i[:2] for i in [n['name'] for n in eval(t4[i])]]
            unique_field = list(set(c))            
            for x in a:
                for y in unique_field:
                    dic[x+'+'+y]+=float(c.count(y))/float(len(c))

t3=[];t4=[];
for i in range(len(value)):
    if value[i] !=0:
        t3.append(key[i])
        t4.append(value[i])#32723

c = sorted(value)
c1=[];c2=[];
for i in c[-11:]:
    a = value.index(i)
    c1.append(key[a])
    c2.append(i)

c3 = [i[:-3] for i in c1]
c3=c3[:-1]

c1=[];c2=[];
for i in tqdm(range(len(key))):    
    if key[i][:-3] in c3:
        c1.append(key[i])
        c2.append(value[i])
        
######################################################################

#################  Supplementary article topics via wikipedia api  ########################
l2=[[],[]]
session = requests.session()
qc = []
for line in open(file of article title,"r",encoding='utf8'): 
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
########################### End ############################################

########### plot cumulative number of nodes per cluster of both networks ################3
l1 = sc.vs['weight'] #sc is super network of co-citation network and sb is super network of bibliographic coupling network
l1 = sorted(l1,reverse=1)
l2 = [sum(l1[:i+1])/sum(l1) for i in range(len(l1))]
l3 = l2
x = [math.log(i,10) for i in l1]
x = [math.log(l1[0],10)-i for  i in x]
## co citation network
fig, ax = plt.subplots(1, 1)
ax.plot(x,l3)
position = 460  #(0.7),size may 
ax.axvline(x[position], color='r', linestyle='--')
plt.text(x[position], l3[position]+0.001, ' %.2f' % (x[position]), ha='left', va= 'top',fontsize=12)
axins = ax.inset_axes((0.61, 0.08, 0.38, 0.3))
zone_left = 100
zone_right = 1000
# 
x_ratio = 0  # 
y_ratio = 0.05  # 

# 
xlim0 = x[zone_left]-(x[zone_right]-x[zone_left])*x_ratio
xlim1 = x[zone_right]+(x[zone_right]-x[zone_left])*x_ratio

# 
y = np.hstack(l3[zone_left:zone_right])
ylim0 = np.min(y)-(np.max(y)-np.min(y))*y_ratio
ylim1 = np.max(y)+(np.max(y)-np.min(y))*y_ratio

# 
axins.set_xlim(xlim0, xlim1)
axins.set_ylim(ylim0, ylim1)
axins.plot(x,l3)
ax.set_ylabel('Share of nodes',fontsize=14)
ax.set_xlabel('log10 cluster size',fontsize=14)
axins.grid()
plt.grid()
#
tx0 = xlim0+0.7
tx1 = xlim1-0.1
ty0 = ylim0+0.15
ty1 = ylim1
sx = [tx0,tx1,tx1,tx0,tx0]
sy = [ty0,ty0,ty1,ty1,ty0]
ax.plot(sx,sy,"black")

# 
xy = (xlim0+0.7,ylim0+0.15)
xy2 = (xlim0,ylim1)
con = ConnectionPatch(xyA=xy2,xyB=xy,coordsA="data",coordsB="data",
        axesA=axins,axesB=ax,color='black')
axins.add_artist(con)

xy = (xlim1-0.1,ylim0+0.15)
xy2 = (xlim1,ylim1)
con = ConnectionPatch(xyA=xy2,xyB=xy,coordsA="data",coordsB="data",
        axesA=axins,axesB=ax,color='black')
axins.add_artist(con)

##########################################################
# bibliographic coupling network
fig, ax = plt.subplots(1, 1)
ax.plot(x,l3)
position = 235  #(0.7),size may 98
ax.axvline(x[position], color='r', linestyle='--')
plt.text(x[position], l3[position]+0.001, ' %.2f' % (x[position]), ha='left', va= 'top',fontsize=12)
axins = ax.inset_axes((0.71, 0.08, 0.28, 0.3))
zone_left = 100
zone_right = 1000
# 
x_ratio = 0  # 
y_ratio = 0.05  # 

# 
xlim0 = x[zone_left]-(x[zone_right]-x[zone_left])*x_ratio
xlim1 = x[zone_right]+(x[zone_right]-x[zone_left])*x_ratio

# 
y = np.hstack(l3[zone_left:zone_right])
ylim0 = np.min(y)-(np.max(y)-np.min(y))*y_ratio
ylim1 = np.max(y)+(np.max(y)-np.min(y))*y_ratio

# 
axins.set_xlim(xlim0, xlim1)
axins.set_ylim(ylim0, ylim1)
axins.plot(x,l3)
ax.set_ylabel('Share of nodes',fontsize=14)
ax.set_xlabel('log10 cluster size',fontsize=14)
axins.grid()
plt.grid()
# 
tx0 = xlim0+0.4
tx1 = xlim1-0.2
ty0 = ylim0-0.03
ty1 = ylim1
sx = [tx0,tx1,tx1,tx0,tx0]
sy = [ty0,ty0,ty1,ty1,ty0]
ax.plot(sx,sy,"black")

# 
xy = (xlim0+0.4,ylim0-0.03)
xy2 = (xlim0,ylim1)
con = ConnectionPatch(xyA=xy2,xyB=xy,coordsA="data",coordsB="data",
        axesA=axins,axesB=ax,color='black')
axins.add_artist(con)

xy = (xlim1-0.2,ylim0-0.03)
xy2 = (xlim1,ylim1)
con = ConnectionPatch(xyA=xy2,xyB=xy,coordsA="data",coordsB="data",
        axesA=axins,axesB=ax,color='black')
axins.add_artist(con)
