# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from django.shortcuts import render
import watson_developer_cloud
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
import urllib2,urllib
from django.http import HttpResponse
import requests
import time
from requests.auth import HTTPBasicAuth
from pymongo import MongoClient
import datetime
import json
import csv

#for opening and extracting values from configuration file
BASE = os.path.dirname(os.path.abspath(__file__))
f= open(os.path.join(BASE, "config.txt"),'r').read()
f=f.split('\n')
uname=f[0].split('=')[1]
pas=f[1].split('=')[1]
ver=f[2].split('=')[1]
env_id=f[3].split('=')[1]
coll_id=f[4].split('=')[1]


#for adding a document
@api_view(['POST'])
def addDocument(request):
    print("in post")
    data=request.data
    fileurl=data["fileurl"]
    fileurl=fileurl.replace(' ','%20')
    discovery = watson_developer_cloud.DiscoveryV1(username=uname,password=pas,version=ver)
    try:
        pdf = urllib2.urlopen(fileurl)
    except urllib2.HTTPError as err:
        return HttpResponse(status=err.code)   
    html_path=pdf.read()
    add_doc = discovery.add_document(env_id,coll_id, file_data=html_path)
    jsonValidateReturn=json.dumps(add_doc)
    return HttpResponse(jsonValidateReturn, content_type='application/json')# ,mimetype='application/json') 
    

@api_view(['GET'])
def get_doc_status(request):
    data=request.query_params
    doc_id=data.keys()[0]
    url="https://gateway.watsonplatform.net/discovery/api/v1/environments/"+env_id +"/collections/"+coll_id +"/documents/"+ doc_id+"?version="+ver
    r=requests.get(url, auth=HTTPBasicAuth(uname,pas))
    print("document status Response sent")
    return HttpResponse(r.content, content_type='application/json')

#for querying values in document
@api_view(['GET'])
def query(request):
    data=request.query_params
    print(data)
    key=data.keys()[0]
    value=data.values()[0]
    print(key)
    print(value)
    discovery = watson_developer_cloud.DiscoveryV1(username=uname,password=pas,version=ver)

    d=key + ":" + value
    print(d)
    query_options = {'query': d }

    obj = discovery.query(env_id,coll_id, query_options)
    
    saveddata=obj
    saveddata.update({"ts":datetime.datetime.now()})
    insertmongo(saveddata)
    entities=obj["results"][0]['enriched_text'] ['entities']
    #value = {'type' : sorted(sort, key=lambda x: x['type'], reverse=False)}

    new_entities=[]
    hashtable=[]

    hashtable.append(entities[0]['type'])
    new_entities.append(entities[0])

    Variant_Only=" "
    model_only_pattern=" "

    for item in entities:
       if not item['type']  in hashtable:
           new_entities.append(item)
           hashtable.append(item['type'])
           if item['type']=='Variant_Only':
               Variant_Only=item['text']
           if item['type']=='model_only_pattern':
               model_only_pattern=item['text']
  
    if 'Engine_Number' not in hashtable:
        if 'engine_number_pattern' in hashtable:
            for item in entities:
                if item['type']=='engine_number_pattern':
                    item['type']='Engine_Number'
                    break

    if 'Chassis_Number' not in hashtable:
        if 'chassis_number_pattern' in hashtable:
            for item in entities:
                if item['type']=='chassis_number_pattern':
                    item['type']='Chassis_Number'
                    break

    if 'Full_Name' not in hashtable:
        if 'name_pattern' in hashtable:
            for item in entities:
                if item['type']=='name_pattern':
                    item['type']='Full_Name'
                    break

    if 'Model_Variant' not in hashtable:
        if 'Variant_Only' in hashtable and 'model_only_pattern' in hashtable:
            for item in entities:
                if item['type']=='Variant_Only':
                    item['type']='Model_Variant'
                    item['text']= Variant_Only + " "+ model_only_pattern
                    break

    jsonValidateReturn=json.dumps(new_entities)
    return HttpResponse(jsonValidateReturn, content_type='application/json')# ,mimetype='application/json')       
    
def insertmongo(data):
    url = 'mongodb://10.0.8.62:27017/'
    client = MongoClient(url)
    db = client.watson
    OcrResponse=db.OcrResponse
    OcrResponse.insert(data)
    print("Inserted")
    return

def convertJsonToCSV(data):
    '''emp_data = '{"employee_details":' + data + '}'
    print(emp_data)
    employee_parsed = json.loads(employee_data)
    emp_data = employee_parsed['employee_details']
    # open a file for writing

    employ_data = open('EmployData.csv', 'w')

    # create the csv writer object

    csvwriter = csv.writer(employ_data)

    count = 0

    for emp in emp_data:
        if count == 0:
            header = emp.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(emp.values())
    employ_data.close()'''

    rows = json.loads(json.dumps(data))
    with open('test.csv', 'wb+') as f:
        dict_writer = csv.DictWriter(f, fieldnames=['count', 'text', 'type'])
        dict_writer.writeheader()
        dict_writer.writerows(rows)

    return

def fileupload(request):
    if request.method=="POST" and "uploadfile" in request.POST:
        print("in post")
        files = request.FILES.getlist('uploads')
        print(files[0])
        print(type(files))
        count=0
        totaldata=[]
        filenames=[]
        discovery = watson_developer_cloud.DiscoveryV1(username=uname,password=pas,version=ver)
        for f in files:
                html_path=f.read()
                add_doc = discovery.add_document(env_id,coll_id, file_data=html_path)
                doc_id=add_doc["document_id"]
                time.sleep(5)
                statusurl="http://10.0.32.94:7000/ocr/docstatus?"+doc_id
                r=requests.get(statusurl)
                data=json.loads(r.content)
                print(data["status"])
                if data["status"] != "available":
                    time.sleep(5)
                url="http://10.0.32.94:7000/ocr/query?_id="+doc_id
                r=requests.get(url)
                count=count+1
                mdata=json.loads(r.content)      
                sort=mdata
                value = {'type' : sorted(sort, key=lambda x: x['type'], reverse=False)}
                totaldata.append(value['type'])
                filenames.append(str(f))     
                convertJsonToCSV(mdata)       
                insertmongo(mdata)
                if len(files)==count:
                   return render(request,'upload.html',{"response":totaldata,"filenames":filenames})

    if request.method=="POST" and "uploadfileurl" in request.POST:
        print("in post")
        fileurl=request.POST.get("fileurl")
        discovery = watson_developer_cloud.DiscoveryV1(username=uname,password=pas,version=ver)
        pdf = urllib2.urlopen(fileurl)
        html_path=pdf.read()
        add_doc = discovery.add_document(env_id,coll_id, file_data=html_path)
        doc_id=add_doc["document_id"]
        time.sleep(5)
        statusurl="http://10.0.32.94:7000/ocr/docstatus?"+doc_id
        r=requests.get(statusurl)
        data=json.loads(r.content)
        print(data["status"])
        if data["status"] != "available":
            time.sleep(5)
        url="http://10.0.32.94:7000/ocr/query?_id="+doc_id
        r=requests.get(url)
        mdata=json.loads(r.content)
        sort=mdata
        value = {'type' : sorted(sort, key=lambda x: x['type'], reverse=False)}
        totaldata=[]
        totaldata.append(value['type'])

        return render(request,'upload.html',{"response":totaldata,"filenames":'Uploaded from URL'})
    return render(request,'upload.html')



            

