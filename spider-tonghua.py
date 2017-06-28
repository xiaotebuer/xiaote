#-*- coding: utf-8 -*-
import urllib
import urllib2
import cookielib
import re,json
import thread,logging.config
import time
import chardet
from bs4 import BeautifulSoup
import db_tonghuashun

start = time.time()
end = start - 3600 * 1

spider_datas = {}
retry = 5

def changeToTimestamp(nowtime):
    #转成时间戳
    time_struct = time.strptime(nowtime,'%Y-%m-%d %H:%M:%S')
    timestamp = time.mktime(time_struct)
    return timestamp

def changeToDateTime(nowtimestamp):
    a = time.localtime(nowtimestamp)
    datetime = time.strftime('%Y-%m-%d %H:%M:%S',a)
    return datetime
    
def getHtml(url,headers={}):
    try:
        logger.info("read html start:%s" %time.time() )  
        request = urllib2.Request(url,headers=headers)
        response = urllib2.urlopen(request) 
        #print response.headers
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
    new_tag_data = soup.find("ul",attrs={"class":re.compile("news_tag news_tag_inlist news_tag")})
    if new_tag_data != None:
        new_tag = int(new_tag_data["class"][2][len("news_tag"):])
        new_tag_list = ["利好","利好","中性","利空","利空"]
        spider_datas["status"] = new_tag_list[new_tag-1]
    else :
        spider_datas["status"] = ""
        
    print spider_datas["status"] 
    info = soup.find_all("div",attrs={"class":"module-l fl"}) #头部内容
    if len(info) == 2:
        info = info[1]
    else:
        info = info[0]

    time = info.find("span",attrs={"class":"time"}) #发布时间
    print time
    
    source = info.find_all("span")[1].find("a") #来源 
    if source != None :
        spider_datas["source"] = source.string
    else :
        spider_datas["source"] = ""
    print spider_datas["source"]
        
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

    datas = soup.find("div",attrs={"class":"atc-content"})

    try :        
        clearfix = datas.find_all("script") #次日走势和最高盈利预测
        print "clearfix:",clearfix
    
        if len(clearfix) !=0 and clearfix[0].string.find("var tcinfo") >= 0:
            #因为这是一个js加载的内容，无法直接读取静态的网页内容获得次日走势，通过拼的url可以获得一个返回的json串，从而得到次日走势和最高盈利预测
            tmp_str = clearfix[0].string.encode('utf-8')
            encrypt = tmp_str[tmp_str.find("\""):].replace("\"","").replace(" ","")
            encrypt_html = "http://m.10jqka.com.cn/wapapi/similar/getSimilar/" + encrypt
            logger.info("获得js加载跳转的网页:%s" %encrypt_html)
            response = getHtml(encrypt_html,headers={"Content-Type":"application/json; charset=utf-8"})
            content = response.read()
            logger.info("获得js加载返回的内容:%s" %content)
            json_content = content[len("similarData("):len(content)-1]
            json_str = json.loads(json_content)
            trend = json_str["slide"]["nextDayForecast"]["numPercent"]
            profit = json_str["slide"]["maxGainsForecast"]["numPercent"]
            pattern = re.compile('.*<span.*>(.*?)<.*',re.S )   
            spider_datas["trend"] = re.findall(pattern,trend)[0].encode('utf-8')
            spider_datas["profit"] = re.findall(pattern,profit)[0].encode('utf-8')

    except Exception as e:
        logger.error("获得次日走势等内容出错:%s" %e)
    finally:
        if not spider_datas.has_key("trend"):
            spider_datas["trend"] = ""
        if not spider_datas.has_key("profit"):
            spider_datas["profit"] = ""                        
            
    article_details = ""
    for data in datas.find_all("p"):
        tmp = ""
        if not data.has_attr("class") :
            for content in data.contents:
                if content.string != None:
                    tmp += content.string
            article_details += tmp
    logger.info("文章详情:%s" %article_details.encode('utf-8') )
    spider_datas["details"] = article_details
    print article_details
    
def getContent(content):
    soup = BeautifulSoup(content,'html5lib')
    loop =3
    while True:
        try :
            if loop <=0 :
                logger.info("读首页列表:%s" %e.message)
                break
            arc_list = soup.find("div",class_="list-con")
            datas = arc_list.find_all("span",attrs={"class":"arc-title"})
            break
        except Exception as e:
            loop -=1
            time.sleep(5)
            continue    
    for data in datas :
        try :
            #标题内容
            article_heading = data.find("a")["title"]
            #获得文章的链接
            url_child = data.find("a")["href"].encode('utf-8')
            print url_child
            logger.info("具体内容的网页链接:%s" %url_child)
            
            logger.info("主标题:%s" %article_heading.encode('utf-8') )
            spider_datas["heading"] = article_heading   
            
            #test
            #url_child = 'http://stock.10jqka.com.cn/20170627/c598998302.shtml'
            child_content = getHtml(url_child)
            #获得文章正文内容
            getChildContent(child_content.read())
            print spider_datas
        
            if spider_datas.has_key("timestamp") and spider_datas["timestamp"] > end :
                logger.info("读写数据库")
                db_tonghuashun.connect_db(spider_datas)
        
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
    sect_url = 'http://stock.10jqka.com.cn/hsdp_list/index'    

    for i in range(1,2) : #剩余页面上的内容
        if i==1 :
            url = sect_url + '.shtml' 
        else:
            url = sect_url + '_' + str(i) + '.shtml' 
        print url
        logger.info("url:%s read start:%s" %(url,time.time()) )
        response = getHtml(url,headers={"Content-Type": "text/html; charset=gbk"})#,headers={"Cookie":"UM_distinctid=15ce366ab5920e-06f5c9505-4e46072c-1fa400-15ce366ab5a8fa"})
        loop =3
        while True:
            try :
                if loop <=0 :
                    logger.info("读列表出错:%s" %e.message)
                    break
                content = response.read().decode('gbk')
                break
            except Exception as e:
                loop -=1
                time.sleep(5)
                continue
            
        logger.info("url:%s read end:%s" %(url,time.time()) )
        getContent(content)

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