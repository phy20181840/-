from lxml import etree
import requests
import json
import datetime

#文件操作
time = str(datetime.datetime.now())
time = time.replace(" ","_")
day_file_path ="/var/www/html/data/weibo/"+time[:10]+".json"
day_file_str=""
try:
    with open(day_file_path,mode='r',encoding='utf-8') as ff:
        day_file_str=ff.read()
except FileNotFoundError:
    with open(day_file_path, mode='w', encoding='utf-8') as ff:
        ff.write("{}")
day_info=json.loads(day_file_str)
#day_file_path="/var/www/html/data/"+time+".json"


#请求信息
url = "https://s.weibo.com/top/summary?cate=realtimehot"
header={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

#爬取数据
response = requests.get(url,headers = header)
html=response.content.decode('utf-8')
elements = etree.HTML(html)

#热搜列表
title_list = elements.xpath('//td[@class="td-02"]/a/text()')[1:]
href_list=[]
for title in title_list:
    href_list.append("https://s.weibo.com/weibo?q=%23"+title+"%23&Refer=top")
view_list = elements.xpath('//td[@class="td-02"]/span/text()')
#import pandas as pd
#df = pd.DataFrame({'热搜名':title_list,'访问次数':view_list,'链接':href_list})
#print(df)

#分别爬取每个热搜的数据
pic_list=[]
comment_list=[]
like_list=[]
tran_list=[]
id_list=[]
cont_list=[]


for i in range(len(href_list)):

    url=href_list[i]
    response = requests.get(url,headers = header)
    html=response.content.decode('utf-8')
    elements = etree.HTML(html)
    etree.strip_tags(elements,'em')

    #转发量
    trans=[]

    #评论数
    comments=[]

    #点赞数
    likes=[]

    #博主名字
    ids=[]

    #微博内容
    temps=[]
    contents=[]

    #图片
    pics=[]

    #视频
    videos=[]

    cards=elements.xpath('.//div[@class="card-wrap"]/div[@class="card-top"]//a[text()="热门" or text()="置顶"]/../../following-sibling::div[1]')
    for i in range(len(cards)):
        trans.append(cards[i].xpath('./div[@class="card-act"]/ul/li[2]/a/text()')[0][4:])
        comments.append(cards[i].xpath('./div[@class="card-act"]/ul/li[3]/a/text()')[0][3:])
        likes.append(cards[i].xpath('./div[@class="card-act"]/ul/li[4]/a/text()')[1])#每个card得到的列表中有两个元素
        ids.append(cards[i].xpath('.//div[@class="content"]/p[1]/@nick-name')[0])
        
        #博文数据预处理
        temps=cards[i].xpath('.//div[@class="content"]/p[1]/text()')
        temp_str=""
        for j in range(len(temps)):
            temp_str=temp_str+temps[j]
        temp_str=temp_str.replace(" ","").replace("\n","").replace("\u200b","")
        contents.append(temp_str)
        
        pics.append(cards[i].xpath('./div[@class="card-feed"]//div[@node-type="feed_list_media_prev"]//ul/li/img/@src'))

    pic_list.append(pics)
    id_list.append(ids)
    comment_list.append(comments)
    like_list.append(likes)
    tran_list.append(trans)
    cont_list.append(contents)
    
#整理数据
result={}
for i in range(len(href_list)):
    temp=[]
    temp.append("浏览次数: " +view_list[i])
    for j in range(len(cont_list[i])):
        temp.append({"博主":id_list[i][j],"微博内容":cont_list[i][j],"图片":pic_list[i][j],"转发":tran_list[i][j],"评论":comment_list[i][j],"点赞":like_list[i][j]})
    result[title_list[i]]=temp

#更新热搜
for event in result:
    if(event in day_info):
        if(len(day_info[event])==1):
            day_info[event]=result[event]
        else:    
            r_num=int(result[event][0][6:])
            d_num=int(day_info[event][0][6:])
            if(r_num>d_num):
                day_info[event][0]=result[event][0]
                
            for i in range(len(result[event])-1):
                for j in range(len(day_info[event])-1):
                    if(result[event][i+1]["博主"]==day_info[event][j+1]["博主"]):
                        day_info[event][j+1]=result[event][i+1]
                        break
                    elif(j==(len(day_info[event])-2)):
                        day_info[event].append(result[event][i+1])
    else:
        day_info[event]=result[event]

#热搜数量
info_num=str(len(day_info))+" "
info_num_file_path="/var/www/html/data/weibo/"+time[:10]+"num.txt"
with open(info_num_file_path,'a',encoding='utf-8')as f:
    f.write(info_num)

#写入文件
cont_str = json.dumps(day_info,ensure_ascii=False)
with open(day_file_path,'w',encoding='utf-8')as f:
    f.write(cont_str)