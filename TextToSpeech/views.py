from __future__ import unicode_literals
import requests
from contextlib import closing
import datetime
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
import os.path
import json
import pyodbc
import xml.etree.ElementTree as ET
from django.http import HttpResponseRedirect
from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
import base64
from django.contrib.auth import authenticate
import urllib

BASE = os.path.dirname(os.path.abspath(__file__))

def save_res(leadId,customerId,Policyno,Insurer,mobileno,url,sid):
    f= open(os.path.join(BASE, "configurations/databaseconfig.txt"),'r').read()
    f=f.split('\n')
    username=f[0].split(':')[1]
    password=f[1].split(':')[1]
    db=f[2].split(':')[1]
    datasource=f[3].split(':')[1]
    con_string ='DRIVER=FreeTDS;DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (datasource, username, password ,db)
    conn = pyodbc.connect(con_string)
    cursor = conn.cursor()
    url=url+"&filename=xyz.mp3"    
    query="INSERT INTO PBCROMA.MTX.VOICEURLDATA(callsid,leadid,customerid,policyno,insurer,mobileno,url) VALUES ('"+sid+"',"+leadId+","+customerId+",'"+Policyno+"','"+Insurer+"',"+mobileno+",'"+url+"');"
    cursor.execute(query)
    conn.commit()
    print("saved to database")
    return


def geturl(filename,leadId,customerId):
    url = "https://api.policybazaar.com/cs/repo/uploadPolicyCopy?metaDataJson={leadId:"+leadId+",customerId:"+customerId+",productId:0,referenceNo:0}"
    files = {'file': (filename,open(filename, 'rb'),'audio/mp3')}
    r = requests.post(url,files=files)
    print(r)
    doc=json.loads(r.content)
    docurl=doc["policyCopyDetails"]["policyDocUrl"]
    return docurl


def save_polly(policyno, insurer,leadid,customerId):
        f= open(os.path.join(BASE, "configurations/userconfig.txt"),'r').read()
        f=f.split('\n')
        region=f[0].split('$')[1]
        accesskey=f[1].split('$')[1]
        secretkey=f[2].split('$')[1]
        session = Session(region_name=region,aws_access_key_id=accesskey,aws_secret_access_key=secretkey)
        polly = session.client("polly")
        policyno=str(policyno)
        insurer=str(insurer)
        f= open(os.path.join(BASE, "configurations/speechconfig.txt"),'r').read()
        f=f.split('$')
        text = f[0]+insurer+f[1]+policyno+f[2]
        response = polly.synthesize_speech(Text=text,VoiceId="Raveena",OutputFormat="mp3",TextType="ssml")
        stream=response.get("AudioStream")
        if stream:
            data=stream.read()
            filename=os.path.join(BASE, "voices/"+policyno+str(datetime.datetime.now())+".mp3")
            filename=filename.replace(" ", "")
            with open(filename, 'wb') as f:
                f.write(data)
                print("File Saved")
                f.close()
            docurl=geturl(filename,leadid,customerId)
            obj={
                "docurl":docurl,
                "filename":filename
            }
            return obj


def give_a_call(mobileno,appidsource=''):  
    f= open(os.path.join(BASE, "configurations/exotelconfig.txt"),'r')
    f=f.read().split('\n')
    if appidsource=='':
        appid=f[0].split('=')[1]
    else:
        appid=f[5].split('=')[1]
    
    print('appid', appid)
    url=f[1].split('=')[1]
    CallerId=f[2].split('=')[1]
    CallType=f[3].split('=')[1]
    auth=f[4].split('=')[1]

    print("calling calling calling.....")
    
    headers = {
               "Authorization":auth,
               "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
               "From":mobileno,
               "CallerId":CallerId,
               "Url":"http://my.exotel.in/exoml/start/"+appid,
               "CallType": CallType
    }
    r=requests.post(url, headers=headers, data=payload)
    print(r)
    res=r.content
    root = ET.fromstring(res)
    sid=root[0][0].text
    print(sid)    
    return sid


@api_view(['POST'])
def pollyexotel(request):
    data=request.data
    try:
        leadId=data["leadId"]
        customerId=data["customerId"]
        policyno=data["policyno"]
        insurer=data["insurer"]
        mobileno=data["mobileno"]
    except:
        return HttpResponse(status=400)
    obj=save_polly(policyno,insurer,leadId,customerId)
    sid=give_a_call(mobileno)
    url=obj["docurl"]
    filename=obj["filename"]
    save_res(leadId,customerId,policyno,insurer,mobileno,url,sid)   
    return Response(status=status.HTTP_200_OK)

@api_view(['POST'])
def samedayexpiryIVR(request):    
    data=request.data
    try:
        leadId=data["leadId"]
        customerId=data["customerId"]        
        mobileno=data["mobileno"]
    except:
        return HttpResponse(status=400)    
    sid=give_a_call(mobileno,"SDE")  
    save_res(leadId,customerId,'','',mobileno,'',sid)   
    return Response(status=status.HTTP_200_OK)    


@api_view(['GET'])
def get_url(request):
         try:
             auth_header = request.META['HTTP_AUTHORIZATION']
         except:
             return HttpResponse(status=401)
         encoded_credentials = auth_header.split(' ')[1]
         decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
         username = decoded_credentials[0]
         password = decoded_credentials[1]
         feed_bot = authenticate(username=username, password=password)
         if(feed_bot):
             f= open(os.path.join(BASE, "configurations/databaseconfig.txt"),'r').read()
             f=f.split('\n')
             username=f[0].split(':')[1]
             password=f[1].split(':')[1]
             db=f[2].split(':')[1]
             datasource=f[3].split(':')[1]
             con_string ='DRIVER=FreeTDS;DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (datasource, username, password,db)
             try:
                 conn = pyodbc.connect(con_string)
             except:
                 return HttpResponse("Failed to connect to database",content_type="text/plain")
             cursor = conn.cursor()
             data=request.query_params
             callsid=data['CallSid']
             print(callsid)
             cursor.execute("SELECT URL FROM PBCROMA.MTX.VOICEURLDATA (nolock) WHERE callsid='"+callsid+"';")
             t=cursor.fetchone()
             if t==None:
                 return HttpResponse("No data found in the database for given sid "+callsid,content_type="text/plain")
             return HttpResponse(t[0], content_type='text/plain')
         return HttpResponse(status=401)

@api_view(['GET'])
def saveExotelResponse(request):
         try:
             auth_header = request.META['HTTP_AUTHORIZATION']
         except:
             return HttpResponse(status=401)
         encoded_credentials = auth_header.split(' ')[1]
         decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
         username = decoded_credentials[0]
         password = decoded_credentials[1]
         feed_bot = authenticate(username=username, password=password)
         if(feed_bot):
             try:
                 data=request.query_params
                 callSid=data['CallSid']
                 DialCallDuration=data['DialCallDuration']
                 EndTime=data['EndTime']
                 CallType=data['CallType']
                 flow_id=data['flow_id']
                 RecordingUrl=data['RecordingUrl']
                 digits=data['digits']
                 CurrentTime=data['CurrentTime']
             except:
                 return HttpResponse(status=400)

             EndTime=urllib.unquote(EndTime)
             digits=urllib.unquote(digits)
             digits=digits.replace("\"","")
             CurrentTime=urllib.unquote(CurrentTime)   
               
             f= open(os.path.join(BASE, "configurations/databaseconfig.txt"),'r').read()
             f=f.split('\n')
             username=f[0].split(':')[1]
             password=f[1].split(':')[1]
             db=f[2].split(':')[1]
             datasource=f[3].split(':')[1]
             con_string ='DRIVER=FreeTDS;DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (datasource, username, password ,db)
             conn = pyodbc.connect(con_string)
             cursor = conn.cursor()

             cursor.execute("SELECT * FROM PBCROMA.MTX.VOICEURLDATA (nolock) WHERE callsid='"+callsid+"';")
             query_result=cursor.fetchone()

             if query_result==None:
                print("No result is found for given Sid")
             else:
                print("The given sid is already present in the database")



             query="INSERT INTO PBCROMA.MTX.VoiceUrlData_Response(callsid,duration,endtime,flowid,url,custresponse,currenttime,calltype) VALUES ('"+callSid+"','"+DialCallDuration+"','"+EndTime+"','"+flow_id+"','"+RecordingUrl+"','"+digits+"','"+CurrentTime+"','"+CallType+"');"
             print(query)
             cursor.execute(query)
             conn.commit()
             return HttpResponse(status=200)
         return HttpResponse(status=401)


@api_view(['POST'])
def getfinaldetails(request):
    data=request.data
    print(data)
    callSid=data['callsid']
    print(callSid)
    url="https://policybazaar2:d147cbf154e05ffeca727caf197ad6db24b6f24f@twilix.exotel.in/v1/Accounts/policybazaar2/Calls/"+callSid
    print(url)
    r=requests.get(url)
    print(r.content)
    root = ET.fromstring(r.content)
    duration=root[0][11].text
    print(duration)

    f= open(os.path.join(BASE, "configurations/databaseconfig.txt"),'r').read()
    f=f.split('\n')
    username=f[0].split(':')[1]
    password=f[1].split(':')[1]
    db=f[2].split(':')[1]
    datasource=f[3].split(':')[1]
    con_string ='DRIVER=FreeTDS;DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (datasource, username, password ,db)
    conn = pyodbc.connect(con_string)
    cursor = conn.cursor()
    query="INSERT INTO PBCROMA.MTX.VoiceUrlData_Response(callsid,duration) VALUES ('"+callSid+"','"+duration+"');"
    print(query)
    cursor.execute(query)
    conn.commit()



    return HttpResponse(status=200)