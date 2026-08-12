from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path('', views.index, name='index'),
    path('subjects/', views.subject_select, name='subject_select'),
    
    # トピック一覧画面 (Math / English)
    path('topics/<str:subject>/', views.topic_list, name='topic_list'),
    path('topics/<str:subject>/add/', views.add_topic, name='add_topic'),
    
    # リンクエラー防止用の仮URL
    path('chat/start/', views.ai_chat_start, name='ai_chat_start'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
]
