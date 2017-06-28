#-*- coding: utf-8 -*-
import urllib
import urllib2
import re,json
import thread,logging.config
import time
import chardet
from bs4 import BeautifulSoup
import db

start = time.time()
end = start - 3600 * 4

firsttimestamp = 20170619747999983
tmptime = firsttimestamp
spider_datas = {}
retry = 3

def changeToTimestamp(nowtime):
    #转成时间戳
    time_struct = time.strptime(nowtime,'%Y年%m月%d日 %H:%M')
    timestamp = time.mktime(time_struct)
    return timestamp

def changeToDateTime(nowtimestamp):
    a = time.localtime(nowtimestamp)
    datetime = time.strftime('%Y-%m-%d %H:%M:%S',a)
    return datetime
    
def getHtml(url):
    try:
        logger.info("read html start:%s" %time.time() )
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        return response
    except urllib2.URLError, e:
        if hasattr(e,"code"):
            print e.code
        if hasattr(e,"reason"):
            print e.reason
        if hasattr(e,"message"):
            print e.message
    finally:
        logger.info("read html end:%s" %time.time() )

def getChildContent(content):
    global retry
    soup = BeautifulSoup(content,'html5lib')
    info = soup.find("div",attrs={"class":"Info"}) #头部内容
    time = info.find("div",attrs={"class":"time"}) #发布时间
    source = info.find("div",attrs={"class":"source"}) #来源  
    author = info.find("div",attrs={"class":"author"}) #作者
    edit_datas = info.find_all("span") #作者
    edit = "None"
    for item in edit_datas :
        if item.contents[0].find(u"编辑") >=0 :
            edit = item.contents[1].string
            logger.info("edit:%s" %edit )
            break
        
    article_time = time.string
    spider_datas["timestamp"] = changeToTimestamp(str(article_time.encode('utf-8')))
    spider_datas["time"] = changeToDateTime(spider_datas["timestamp"])
    logger.info("时间:%s" %article_time.encode('utf-8'))
    
    if spider_datas["timestamp"] <= end :
        e = "增量结束"
        print retry
        if retry ==0 :
            raise Exception(e)        
        else:
            retry = retry -1
            logger.info("retry:%s" %retry )
            pass            
        
    article_source = source.img["alt"]
    logger.info("来源:%s" %article_source.encode('utf-8'))
    spider_datas["source"] = article_source
    
    if author != None :
        article_author = author.string.replace(u"作者：","")
    else :
        article_author = edit
    spider_datas["author"] = article_author
    logger.info("作者:%s" %article_author.encode('utf-8'))

    datas = soup.find("div",attrs={"id":"ContentBody"})
    article_details = ""
    for data in datas.find_all("p"):
        tmp = ""
        for content in data.contents:
            if content.string != None:
                tmp += content.string
        article_details += tmp
    logger.info("文章详情:%s" %article_details.encode('utf-8') )
    spider_datas["details"] = article_details

def getPageNo(page):
    soup = BeautifulSoup(page,'html5lib')
    pages_item = soup.find("div",attrs={"id":"pagerNoDiv","class":"pager"})
    pages = pages_item.find_all("a")
    return pages[len(pages)-2].string
    
def getContent(content):
    soup = BeautifulSoup(content,'html5lib')
    datas = soup.find_all(id=re.compile("newsTr"))
    for data in datas :
        try :
            data1 = data.find("p",attrs={"class":"title"})
            data2 = data.find("p",attrs={"class":"info"})
            
            #获得文章的链接
            url_child = str(data1.find("a")["href"])
            logger.info("具体内容的网页链接:%s" %url_child)
            ''''
            pattern = re.compile(".*?,(.*?).html")
            items = re.findall(pattern,url_child)
            timestamp = int(items[0])
            print "timestamp:",timestamp
            if timestamp > tmptime :
                firsttimestamp_after = timestamp
            if timestamp <= firsttimestamp :
                e = "增量结束"
                raise Exception(e)
            '''
            
            #标题内容
            article_heading = data1.find("a").string.replace("\n","")
            logger.info("主标题:%s" %article_heading.encode('utf-8') )
            if data2.has_attr("title") :
                article_subheading = data2["title"].replace("\t","")
                logger.info("副标题:%s" %article_subheading.encode('utf-8'))
            else:
                article_subheading = data2.string.replace("\t","")
                logger.info("副标题:%s" %article_subheading.encode('utf-8'))
            
            spider_datas["heading"] = article_heading
            spider_datas["subheading"] = article_subheading        
    
            child_content = getHtml(url_child)
            #获得文章正文内容
            getChildContent(child_content.read())
    
            if spider_datas.has_key("timestamp") and spider_datas["timestamp"] > end :
                logger.info("读写数据库")
                db.connect_db(spider_datas)
                spider_datas.clear()
                logger.info("spider_datas:%s" %spider_datas)
                #print "时间:",data.find("p",attrs={"class":"time"}).string
        except Exception as e:
            if e.message == "增量结束" :
                raise e 
            else:
                logger.error("出错:%s" %e)
                spider_datas.clear()
                continue            

def readPages():
    logger.info("read start:%s" %time.time() )
    #sect_url = 'http://stock.eastmoney.com/news/'
    #mainurl = 'http://stock.eastmoney.com/news/cdpfx.html'
    sect_url = 'http://stock.eastmoney.com/news/'
    mainurl = 'http://stock.eastmoney.com/news/cggdd.html'
    response = getHtml(mainurl)
    content = response.read()
    logger.info("read end:%s" %time.time() )
    page_number = int(getPageNo(content))
    
    getContent(content) #第一个页面上的内容  
    
    for i in range(2,page_number+1) : #剩余页面上的内容
        url = sect_url + 'cdpfx_' + str(i) + '.html' 
        logger.info("url:%s read start:%s" %(url,time.time()) )
        response = getHtml(url)
        content = response.read()
        logger.info("url:%s read end:%s" %(url,time.time()) )
        getContent(content)  

#pattern = re.compile('<li id="newsTr.*?">.*?<p class="info" title="(.*?)">(.*?)</p>',re.S )   
#items = re.findall(pattern,content)
#for item in items:
    ##print item[0].decode('GB2312'),item[1].decode('GB2312')
    #print item[0] ,item[1]

if __name__ == '__main__':
    logging.config.fileConfig('F:\\automator_python\\spider\\logging.conf', disable_existing_loggers=False)  
    logger = logging.getLogger('main')
    logger.info("spider start:%s" %time.time())
    try :
        readPages()
    except Exception as e :
        if e.message == "增量结束" :
            logger.error("出错:%s" %e)
        else:
            raise e 
    logger.info("spider end:%s" %time.time())