from django.urls import path
from . import views

app_name = "learning"

urlpatterns = [
    path("", views.index, name="index"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("material/create/", views.create_material_view, name="create_material"),
    path("path/generate/", views.generate_path_view, name="generate_path"),
    path("checkpoint/submit/", views.submit_checkpoint_view, name="submit_checkpoint"),
    path("hint/<int:question_id>/<int:level>/", views.get_hint_view, name="get_hint"),
    path("chat/", views.chat_view, name="chat"),
]
