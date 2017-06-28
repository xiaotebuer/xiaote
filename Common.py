#-*- coding: utf-8 -*-
"""
  Author:   JinMeng
  Created:  11/22/16
"""
#共通方法
#=======================================
import json
import urllib,urllib2,cookielib ,chardet
import threading

def set_logger(my_logger):
    global logger
    logger = my_logger["Common"]

def get_http(host,port,url,data,method,headers={},request_type="urlencoded"):
    #http_method表示http请求，"get","get/post","put","delete"
    response = http_request(host, port, url, data, method,headers=headers,request_type=request_type)
    he = get_http_header(response)
    logger[threading.current_thread().name].info("cookie:%s"%he)
    return get_response_dict(response)

def get_http_header(response):
    header = response.info().getheader('Set-Cookie')  
    return header

def get_http_code(response):
    code = response.code
    return code

def http_request(host,port,url,data,http_method,headers={},request_type="urlencoded"):
    #http请求的共通方法
    if port != "":
        port = ':' + str(port) 
    logger[threading.current_thread().name].info("type data:%s,data:%s"%(type(data),data)) 
    logger[threading.current_thread().name].info("request_type:%s"%request_type)
    url = host + str(port) + url
    if request_type == "urlencoded" :
        data = urllib.urlencode(data)
    elif request_type != "str":
        data = json.dumps(data)
        logger[threading.current_thread().name].info(data)
        if request_type == "form-data" :
            headers = {"Content-Type":"multipart/form-data"}
        if request_type == "json" :
            headers = {"Content-Type":"application/json"}    
        if request_type == "text" :
            headers = {"Content-Type":"application/text"}
        if request_type == "xml" :
            headers = {"Content-Type":"application/xml"}
        if request_type == "html" :
            headers = {"Content-Type":"application/html"}
    if http_method == "get":
        #如果是get请求的话
        if data :     
            url = url + '?'+ data
        data = None

    logger[threading.current_thread().name].info("url:%s,data:%s,http_method:%s"%(url,data,http_method))
    try:
        request = urllib2.Request(url,data =data,headers = headers)   
        if http_method == "put":
            request.get_method = lambda: 'PUT'
        if http_method == "delete":
            request.get_method = lambda: 'DELETE'
        response = urllib2.urlopen(request,timeout = 10)
        #logger[threading.current_thread().name].info("request response:%s" %response)
        return response
    except Exception as e:
        logger[threading.current_thread().name].error("http通信异常:%s"%e)
        raise e    

def get_response_dict(response):
    #logger[threading.current_thread().name].info("get request response:%s" %response)
    res_datas = response.read()
    #返回的数据进行编码
    rec_code = "chardet.detect(res_dict):",chardet.detect(res_datas)
    rec_code = rec_code[1]['encoding']
    res = res_datas.decode(rec_code,'ignore')
    res_dict = json.loads(res_datas,encoding =rec_code)
    logger[threading.current_thread().name].info("response:%s" %res.encode('utf-8','ignore'))
    return res_dict
    
def get_socket(ts,protocol,data):
    try:
        ts.SendMsg(str(data),int(protocol))
        response=ts.RevMsg()
        #返回的数据进行编码
        rec_code = "chardet.detect(res_dict):",chardet.detect(response)
        rec_code = rec_code[1]['encoding']
        res = response.decode(rec_code)

        res_dict = json.loads(response,encoding =rec_code)
        logger[threading.current_thread().name].info("response:%s" %res.encode('utf-8','ignore'))

        return res_dict
    except Exception as e:
        ts.Close()
        logger[threading.current_thread().name].error("socket通信异常:%s"%e) 
        raise e
