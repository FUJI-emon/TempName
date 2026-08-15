from django.urls import path
from . import views

app_name = "learning"

urlpatterns = [
    path("", views.index, name="index"),
    path("navigation.js", views.frontend_navigation_js, name="frontend_navigation_js"),
    path("lumina_learning_landing_page.html", views.frontend_page, {"page_name": "lumina_learning_landing_page.html"}, name="landing_page"),
    path("lumina_learning_login_screen.html", views.frontend_page, {"page_name": "lumina_learning_login_screen.html"}, name="login_page"),
    path("student_dashboard_overview.html", views.frontend_page, {"page_name": "student_dashboard_overview.html"}, name="dashboard_page"),
    path("lumina_learning_upload_document_desktop.html", views.frontend_page, {"page_name": "lumina_learning_upload_document_desktop.html"}, name="upload_page"),
    path("review_document_content_selection.html", views.frontend_page, {"page_name": "review_document_content_selection.html"}, name="review_document_page"),
    path("personalized_learning_path.html", views.frontend_page, {"page_name": "personalized_learning_path.html"}, name="learning_path_page"),
    path("interactive_lesson_linear_regression_with_sidebar.html", views.frontend_page, {"page_name": "interactive_lesson_linear_regression_with_sidebar.html"}, name="lesson_page"),
    path("new_course_ai_topic_discussion.html", views.frontend_page, {"page_name": "new_course_ai_topic_discussion.html"}, name="ai_tutor_page"),
    path("settings_user_account_preferences.html", views.frontend_page, {"page_name": "settings_user_account_preferences.html"}, name="settings_page"),
    path("course_history_my_learning_journeys_1.html", views.frontend_page, {"page_name": "course_history_my_learning_journeys_1.html"}, name="history_page"),
    path("final_test_full_screen_question_review.html", views.frontend_page, {"page_name": "final_test_full_screen_question_review.html"}, name="test_page"),
    path("final_test_result_summary_review.html", views.frontend_page, {"page_name": "final_test_result_summary_review.html"}, name="result_page"),
    path("final_test_ai_review_conversation.html", views.frontend_page, {"page_name": "final_test_ai_review_conversation.html"}, name="ai_review_page"),
    path("onboarding/", views.onboarding_view, name="onboarding"),
    path("material/create/", views.create_material_view, name="create_material"),
    path("path/generate/", views.generate_path_view, name="generate_path"),
    path("checkpoint/submit/", views.submit_checkpoint_view, name="submit_checkpoint"),
    path("hint/<int:question_id>/<int:level>/", views.get_hint_view, name="get_hint"),
    path("chat/", views.chat_view, name="chat"),
    path("chat/thread/", views.create_chat_thread_view, name="create_chat_thread"),
    path("auth/register/", views.register_view, name="register"),
    path("auth/login/", views.login_view, name="login"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("auth/me/", views.me_view, name="me"),
]
