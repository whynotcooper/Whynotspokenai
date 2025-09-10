from django.urls import path

from . import views

app_name = 'spoken_ai'



urlpatterns = [
    path('', views.index, name='index'),  # 首页
    path('spoken_ai/', views.spoken_ai, name='spoken_ai'),  # 口语教练
    path('process_audio/', views.process_audio, name='process_audio'),  # 处理音频
    path('finish_session/', views.finish_session, name='finish_session'),
]