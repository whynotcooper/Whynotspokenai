from django.urls import path

from . import views

app_name = 'spoken_ai'






urlpatterns = [
    path('', views.index, name='index'),  # 首页
    path('login/', views.login_view, name='login'),  # 登录页面
    path('logout/', views.logout_view, name='logout'),  # 登出页面  
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
    path('task2/<int:task_id>/process_task_audio/', views.process_task_audio, name='process_task_audio'),
    path('task2/<int:task_id>/analyse_task2/', views.analyse_task2, name='analyse_task2'),
    path('task3/', views.task3_list, name='task3_list'),
    path('task3/<int:task_id>/', views.show_task3, name='show_task3'),
    path('task3/<int:task_id>/process_task_audio/', views.process_task_audio, name='process_task_audio'),
    path('task3/<int:task_id>/analyse_task3/', views.analyse_task3, name='analyse_task3'),
    path('task4/', views.task4_list, name='task4_list'),
    path('task4/<int:task_id>/', views.show_task4, name='show_task4'),
    path('task4/<int:task_id>/process_task_audio/', views.process_task_audio, name='process_task_audio'),
    path('task4/<int:task_id>/analyse_task4/', views.analyse_task4, name='analyse_task4'),
    path('followup/',views.followup,name='followup'),
    path("followup/chat/", views.solve_followup, name="followup_chat"),  # 接收 AJAX
    path('password_reset/', views.password_reset, name='password_reset'),  # 找回密码页面
]  