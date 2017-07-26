from django_hosts import patterns, host
from django.contrib import admin


host_patterns = patterns('',
    host(r'public', 'TextToSpeech.urlp', name='public'),
    host(r'private', 'OCR.urls', name='ocr'),
    #host(r'private', 'TextToSpeech.urls', name='texttospeech'),
)