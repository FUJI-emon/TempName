from django.urls import path
from . import views

app_name = "learning"

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
    path('chat/', views.chat_thread_list, name='chat_thread_list'),
    path('chat/<int:thread_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:thread_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/create/<int:topic_id>/', views.create_chat_thread, name='create_chat_thread'),
    path('topic/<int:topic_id>/step/<int:step_num>/', views.lesson_card_view, name='lesson_card'),
    path('topic/<int:topic_id>/step/<int:step_num>/checkpoint/', views.lesson_checkpoint_view, name='lesson_checkpoint'),
    path('topic/<int:topic_id>/step/<int:step_num>/complete/', views.complete_step_api, name='complete_step_api'),
    path('api/topic/<int:topic_id>/step/<int:step_num>/complete/', views.complete_step_api, name='complete_step_api'),
    path('settings/update/', views.update_settings, name='update_settings'),
    path('settings/', views.settings_view, name='settings'),
    path('profile/', views.profile_view, name='profile'),
    path("", views.index, name="index"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("material/create/", views.create_material_view, name="create_material"),
    path("path/generate/", views.generate_path_view, name="generate_path"),
    path("checkpoint/submit/", views.submit_checkpoint_view, name="submit_checkpoint"),
    path("hint/<int:question_id>/<int:level>/", views.get_hint_view, name="get_hint"),
    path("chat/", views.chat_view, name="chat"),
]
