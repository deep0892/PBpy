from django.conf.urls import url
from TextToSpeech.views import pollyexotel,samedayexpiryIVR,getfinaldetails

urlpatterns = [
    url(r'polly', pollyexotel),    
    url(r'samedayexpiryIVR', samedayexpiryIVR),
    url(r'finalcalldetails', getfinaldetails), 
]
