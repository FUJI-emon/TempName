from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    # 🏠 ログイン前トップページ
    path('', views.index, name='index'),
    
    # 📊 ログイン後ダッシュボード（追加！）
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 教科選択などその他の設定...
    path('subjects/', views.subject_select, name='subject_select'),
    path('topics/<str:subject>/', views.topic_list, name='topic_list'),
    path('topics/<str:subject>/add/', views.add_topic, name='add_topic'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:topic_id>/upload/', views.document_upload, name='document_upload'),
    path('topic/<int:topic_id>/edit-title/', views.edit_topic_title, name='edit_topic_title'),
    path('topic/<int:topic_id>/delete/', views.delete_topic, name='delete_topic'),
    path('topics/<str:subject>/batch-delete/', views.batch_delete_topics, name='batch_delete_topics'),
    path('topic/<int:topic_id>/save-understanding/', views.save_understanding, name='save_understanding'),
    path('topic/<int:topic_id>/path-map/', views.path_map_view, name='path_map'),
    path('finaltest/', views.finaltest, name='finaltest'),
]