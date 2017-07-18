from django.conf.urls import url
from TextToSpeech.views import pollyexotel

urlpatterns = [
    url(r'polly', pollyexotel),
]
