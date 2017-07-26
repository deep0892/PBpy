from django.conf.urls import url
from TextToSpeech.views import pollyexotel,samedayexpiryIVR

urlpatterns = [
    url(r'polly', pollyexotel),    
    url(r'samedayexpiryIVR', samedayexpiryIVR),    
]
