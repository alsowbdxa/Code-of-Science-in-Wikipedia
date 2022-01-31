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
import pickle

tqdm.pandas()
#sns.set(style="darkgrid")

# with the result1 we get from the "input and read the dataset.py", we can creat the co-citation network and bibliographic coupling network and analysis it.
#
# In this file you can find below processes:
#     1. Creat co-citation network and Bibliographic coupling network, and then use leiden algorithm to detect the community and create the super network.
#     2. Integrate supporting datasets to networks (ORES, WikiProjects, FoR) 
#     3. Figures in the paper.

########## create co-citation network matrix start #########################
result = pd.read_parquet('page_doi.parquet') # the result in the step "Input and read the dataset.py"
result_dimension = pd.read_parquet(r'\result_dimension.parquet')#use your own path, "Extracting data from Dimensions.py"
result_topic = pd.read_parquet(r'\page_topic.parquet')#use your own path, "Adding topic from Wikipedia API.py"
#
#wiki project could be get from below link.
#https://figshare.com/articles/dataset/Wikipedia_Articles_and_Associated_WikiProject_Templates/10248344
file = open("labeled_enwiki_with_topics_metadata.json", 'r', encoding='utf-8')
papers = []
for line in file.readlines():
    dic = json.loads(line)
    papers.append(dic)   
title=[]
topic=[]
wk = []
for i in tqdm(papers):
    title.append(i['title'])
    topic.append(i['topics'])
    wk.append(i['wp_templates'])
dic = dict(zip(title,wk))
def clean(x):
    try:
        return dic[x]
    except:
        return np.nan
result['wk_project'] = result['page_title'].progress_apply(lambda x:clean(x))
#with open('', 'wb') as f:
#    pickle.dump(dic, f, pickle.HIGHEST_PROTOCOL)   
#with open('', 'rb') as f:
#    test = pickle.load(f)
########################################################

#co-citation network
g1 = result.groupby('page_title')
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
for x in tqdm(edge_list):
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

g_cocitation = g
c_cocitation = cluster_solution
s_cocitation = super_graph

to_delete_ids = [v.index for v in s1.vs if v.degree() == 0]
super_graph.delete_vertices(to_delete_ids)# co-citation node:31515
ig.write(super_graph,file_name,format='gml') #use this file in Gephi and draw the co-citation network plot
############# co-citation network end #######################################

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
super_graph = cluster_solution.cluster_graph(combine_vertices={'weight': 'sum'},combine_edges={'weight': 'sum'})
super_graph.vcount()

g_biblio = g
c_biblio = cluster_solution
s_biblio = super_graph

tb = [v.index for v in super_graph.vs if v.degree() == 0]
super_graph.delete_vertices(tb)

ig.write(super_graph,file_name,format='gml') #use this file in Gephi and draw the bibliographic coupling network plot

testread = ig.read(file_name,format='gml')
########## Bibliographic coupling network end ####################

############# analysis network start #############
# Bibliographic coupling network
#### calculate each cluster's macro topic ######################
def top_macro(cate):# use the top1 macro topic to represent the cluster
    l1 = [eval(i)[0] for i in cate]#topic list
    l2 = [eval(i)[1] for i in cate]#score list
    l3 = [x.split('.')[0] for a in l1 for x in a]#macro topic
    l4 = [x for i in l2 for x in i]
    frames1 = [pd.DataFrame(i) for i in [l3,l4]]
    result = pd.concat(frames1,axis=1)
    result.columns=['topic','score']
    l5 = result.groupby('topic')
    l6 = [(i[0],sum(i[1]['score'])) for i in l5]
    l7 = sorted(l6,key = lambda x:x[1],reverse=1)
    return l7[0]
page_topic = dict(zip(result.page_title,result.new_topic))
top_topic=[]
top_score=[]
lack=[]
for i in tqdm(c_biblio):
    page = [g_biblio.vs[x]['name'] for x in i]
    cate = [page_topic[n] for n in page if (page_topic[n] != np.nan) and (len(page_topic[n])>2)]
    try:
        top = top_macro(cate)
        top_topic.append(top[0])
        top_score.append(top[1])
    except:
        top_topic.append('')
        top_score.append('')
        lack.append((list(c_biblio).index(i),page))
############################################################

######### calculate each cluster's frequent wk_project ############
def top_macro(cate):# use the top1 wk_project to represent the cluster
    l1 = [i['name'] for i in cate]
    c = Counter(l1)
    wp = c.most_common(1)[0][0]# 1st wk project
    f = c.most_common(1)[0][1]# frequent
    return [wp,f]
page_wkp = dict(zip(result.page_title,result.wk_project))
top_project=[]
top_f=[]
lack=[]
for i in tqdm(c_biblio):
    page = [g_biblio.vs[x]['name'] for x in i]
    cate = [page_wkp[n] for n in page if (page_wkp[n] is not None) and (len(page_wkp[n])>1)]
    try:
        top = top_macro(cate)
        top_project.append(top[0])
        top_f.append(top[1])
    except:
        top_project.append('')
        top_f.append('')
        lack.append((list(c_biblio).index(i),page))    

#################################################################
###co citation netwrok
def top_macro(cate):# use the top1 FoR to represent the cluster
    #l1 = [x['name'] for i in cate for x in i] 
    l1 = [i for i in cate]   
    c = Counter(l1)
    field = c.most_common(1)[0][0]# 1st field
    f = c.most_common(1)[0][1]# frequent
    return [field,f]

doi_field = dict(zip(result.doi,result.field))
lc = list(c_cocitation)
top_field=[]
top_f=[]
lack=[]

for i in tqdm(c_cocitation):
    page = [g_cocitation.vs[x]['name'] for x in i]
    cate=[]
    for n in page:
        try:
            cate.append(doi_field[n])
        except:
            pass
    try:
        top = top_macro(cate)
        top_field.append(top[0])
        top_f.append(top[1])
    except:
        top_field.append('')
        top_f.append('')
        lack.append((lc.index(i),page))    
###
################### analysis network end ####################


################## 2. Integrate supporting datasets to networks (ORES, WikiProjects, FoR) ###############
#  doi2fields
test = result_dimension[['doi','field']]

t1 = list(test.groupby('doi'))
t2=[]
t3=[]
for i in tqdm(t1):
    t2.append(i[0])
    try:
        a = [n['name'][:2] for n in eval(list(i[1]['field'])[0])]
        c = Counter(a)
        f = c.most_common(1)[0][0]
    except:
        f = 'others'
    t3.append(f)

doi2fields = dict(zip(t2,t3))
#######################################
#  page2topics
test = result_topic[['page_title','new_topic']]
t1 = list(test.groupby('page_title'))
t2=[]
t3=[]

for i in tqdm(t1):
    t2.append(i[0])
    try:
        a = eval(list(i[1]['new_topic'])[0])
        a1 = [m.split('.')[0] for m in a[0]]
        a2 = list(set(a1))
        a3 = [0 for i in a2]
        for x in range(len(a1)):
            a3[a2.index(a1[x])]+=a[1][x]/sum(a[1])
        f = a2[a3.index(max(a3))]
    except:
        f = 'others'
    t3.append(f)

page2topics = dict(zip(t2,t3))
#########################################
# page2wk_projects

test = result[['page_title','wk_project']]

t1 = list(test.groupby('page_title'))
t2=[]
t3=[]

for i in tqdm(t1):
    t2.append(i[0])
    try:
        a = eval(str(list(i[1]['wk_project'])[0]))
        a1 = [m.split('/')[0] for m in a]
        c = Counter(a1)
        f = c.most_common(1)[0][0]
    except:
        f = 'others'
    t3.append(f)

page2wk_projects = dict(zip(t2,t3))

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

ig.write(super_graph,file_name,format='graphml')#define your file_name
######### add fields to co-citation network end ################

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

ig.write(sb,file_name,format='graphml') # this offers the super network with wikipedia article topics and wikiProjects, could be loaded in the Gephi and analysis. 
# In the Gehpi you could get the figure 12-16
################## 2. Integrate supporting datasets to networks (ORES, WikiProjects, FoR) end ###############



################## 3. Figures in the paper ###############

############### figure 1 start #####################
### "Figure 1:  Number of clusters at varying values of the resolution parameter" 
# to draw the relationship between the resolution and the number of clusters
# use result[['page_title','doi']] and generate the graph as before for each network

n=[i*0.01 for i in range(1,99)]
cluster_num=[]
for i in tqdm(n):
    cluster_solution = g.community_leiden(resolution_parameter=i, n_iterations=2,weights=g.es['weight'],node_weights=g.vs['weight'])
    cluster_num.append(len(cluster_solution))
    
plt.plot(n,cluster_num)
plt.semilogx()
plt.xlabel('Resolution parameter',fontsize = 14)
plt.ylabel('Number of clusters',fontsize = 14)
############### figure 1 end #####################

###  "Figure 2:  Cumulative share of nodes included in the supernetworks, per clustersize threshold" ####
########### plot cumulative number of nodes per cluster of both networks ################
l1 = sc.vs['weight'] #sc is super network of co-citation network and sb is super network of bibliographic coupling network, which could be found above
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
l1 = sb.vs['weight'] #sb is super network of bibliographic coupling network which could be found above
l1 = sorted(l1,reverse=1)
l2 = [sum(l1[:i+1])/sum(l1) for i in range(len(l1))]
l3 = l2
x = [math.log(i,10) for i in l1]
x = [math.log(l1[0],10)-i for  i in x]
fig, ax = plt.subplots(1, 1)
ax.plot(x,l3)
position = 235  #(0.7),size is around 98
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

###  "Figure 2:  Cumulative share of nodes included in the supernetworks, per clustersize threshold" end ####

###  Table 1, Table 2 and Figure 3 ####
test = result_dimension[['doi','field']]
t1=result_dimension['field'].to_list()
t2=[]
for i in tqdm(t1):
    try:
        t2.append(eval(i))
    except:
        t2.append('')
t1 = [i['name'] for x in t2 for i in x]
t3=list(set(t1))
import re
macro=[];micro=[];
for i in t3:
    if len(re.sub('\D','',i))==2:
        macro.append(i) #macro topic
    if len(re.sub('\D','',i))==4:
        micro.append(i) #micro topic

t3.sort()#01,0101,...
dic = dict(zip(t3,[0 for i in range(len(t3))]))

#fractional counting 
for article in tqdm(t2):
    try:
        field = [i['name'] for i in article]
    except:
        continue
    unique_list = list(set(field))
    for i in unique_list:
        dic[i]+=float(field.count(i))/float(len(field))

# fields and unique dois
t1 = list(test.groupby('doi'))
num=0
for i in tqdm(t1):
    try:
        c = eval(i[1]['field'].to_list()[0])
    except:
        num+=1
        continue
    field = [i['name'] for i in c]
    unique_list = list(set(field))
    for i in unique_list:
        dic[i]+=float(field.count(i))/float(len(field))
        
key = list(dic.keys())
value = list(dic.values())     
# num
# Out[61]: 143291    

# recent citation, missing 75248,have 1629837
cited = result_dimension['recent_citation'].to_list()
max(cited)
# Out[66]: 34845.0

np.mean(cited)  # 36.4
np.median(cited) # 5.0

###  Table 1, Table 2 and Figure 3 end ####

###  Figure 4 and 5: River plot ####
# Here we use an online tool to draw the river plot and you can find more details in dycharts.com
############## topic to macro fields ####################################
#d1 = pd.read_parquet(file with wikipedia projects and topics)
#dic = dict(zip(test['doi'],test['fields']))
#tqdm.pandas()
result['fields'] = result['doi'].progress_apply(lambda x:doi2fields[x])
result['new_topic'] = result['page_title'].progress_apply(lambda x:page2topics[x])
t1=result[['new_topic','fields']]
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

################ river plot of wk project and macro fields ###############
#dic = dict(zip(data['doi'],data['wk+topics']))
#d1['wk_project'] = d1['doi'].progress_apply(lambda x:dic[x])
#def clean(x):
#    try:
#        return dic[x]['wk_project']
#    except:
#        return ''
#d1['wk_project'] = d1['doi'].progress_apply(lambda x:clean(x))
t1=result[['wk_project','field']]
t1=t1.dropna(subset=['wk_project'])#1705085
t1=t1.dropna(subset=['field'])  #1629837
t2 = t1['wk_project'].to_list()
t3=[]
for i in tqdm(t2):
    for a in i:
        if a not in t3:
            t3.append(a)  #57684
t3.sort()
t7=[x+'+'+y[:2] for x in t3 for y in macro]

t3 = t1['wk_project'].to_list()
t4 = t1['field'].to_list()

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
        
#Then you can save the result and upload it to dycharts.com to draw the river plots
######################################################################
###  Figure 4 and 5: River plot end ####

###  Figure 6,7 and 8 ####
# top10 clusters' topic and wiki_project in bibliographic coupling network 
l1 = [len(i) for i in c_biblio]
l2 = sorted(l1,reverse=1)
#l2[:10]
l3 = [l1.index(i) for i in l2[:10]]
l4 = [c_biblio(i) for i in l3]
l5 = [[g_biblio.vs[n]['name'] for n in i] for i in l4]#list of top10 cluster and their peag_title

l6 = [[eval(page2topics[n]) for n in i if len(page2topics[n])>1] for i in l5]
top_topic=[];#to save marco topic for top10 cluster
for cluster in tqdm(l6):
    t1 = [n.split('.')[0] for y in cluster if y!=[] for n in y[0]]
    t2 = [n for y in cluster if y!=[] for n in y[1]]
    d = pd.DataFrame({'topic':t1,'score':t2})
    d1 = d.groupby('topic')
    top_topic.append([(i[0],sum(i[1]['score'])) for i in d1])

l7 = [[page2wk_projects[n] for n in i] for i in l5] 
#to save wiki project for top10 cluster
top_project=[Counter(i).most_common() for i in l7]
    
# top FoR of co-citaion network
l1 = [len(i) for i in c_cocitation]
l2 = sorted(l1,reverse=1)
#l2[:10]
l3 = [l1.index(i) for i in l2[:10]]
l4 = [c_cocitation(i) for i in l3]
l5 = [[g_cocitation.vs[n]['name'] for n in i] for i in l4]#list of top10 cluster and their doi

l8 = [[doi2fields[n] for n in i] for i in l5] 
t1 = [[n for i in x for n in i] for x in l8]
top_field = [Counter(i).most_common() for i in t1]

#Create a table with the top-10 Wikipedia pages per cluster 
#(only top-10 cluster, bibliographic coupling), 
#picking the 10 Wikipedia pages with most citations to a DOI.
a0=[[] for _ in range(10) ]
for n in tqdm(range(10)):
    a1=[(i,dic[i]) for i in l5[n]]
    a2 = sorted(a1,reverse=1,key=lambda x:x[1])[:10]                      
    a3=[i[0] for i in a2]
    # a4 = [l5[n][i] for i in a3]
    a0[n].extend(a3)
frames1 = [pd.DataFrame(i) for i in a0]
result3 = pd.concat(frames1,axis=1)
result3.to_excel(file_name,encoding='utf_8_sig')
###  Figure 6,7 and 8 end ####
##########################################################

