from django.conf.urls import url
from OCR.views import addDocument,query,get_doc_status,fileupload
from TextToSpeech.views import pollyexotel

urlpatterns = [
    url(r'adddoc', addDocument),
    url(r'query', query),
    url(r'docstatus', get_doc_status),
    url(r'upload', fileupload),
    url(r'polly', pollyexotel),    

]
