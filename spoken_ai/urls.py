from django.urls import path

from . import views

app_name = 'spoken_ai'






urlpatterns = [
    path('', views.index, name='index'),  # 首页
    path('spoken_ai/', views.spoken_ai, name='spoken_ai'),  # 口语教练
    path('process_audio/', views.process_audio, name='process_audio'),  # 处理音频
    path('finish_session/', views.finish_session, name='finish_session'),
    path('register/', views.register, name='register'),  # 登录页面
    path('toefl_index/', views.toefl_index, name='toefl_index'),
    path('task1/', views.task1_list, name='task1_list'),
    path('task1/<int:task_id>/', views.show_task1, name='show_task1'),
    path('task1/<int:task_id>/process_task_audio/', views.process_task_audio, name='process_task_audio'),
    path('task1/<int:task_id>/analyse_task1/', views.analyse_task1, name='analyse_task1'),
    path('task2/', views.task2_list, name='task2_list'),
    path('task2/<int:task_id>/', views.show_task2, name='show_task2'),
    path('followup/',views.followup,name='followup'),
    path("followup/chat/", views.solve_followup, name="followup_chat"),  # 接收 AJAX
]  