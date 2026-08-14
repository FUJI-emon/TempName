from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    # もともとあったトップページの設定
    path('', views.index, name='index'),
    
    # 今回新しく追加したFinal Testの設定
    path('finaltest/', views.finaltest, name='finaltest'),
]