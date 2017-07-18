from django.conf.urls import url
from TextToSpeech.views import get_url,saveExotelResponse

urlpatterns = [
    url(r'geturl', get_url),
    url(r'callresponse', saveExotelResponse),
]
