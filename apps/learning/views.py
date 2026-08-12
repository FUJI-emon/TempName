from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import LearningMaterial


def index(request):
    """
    Homepage view for the learning app.
    Displays project educational vision and current registered learning materials.
    """
    materials = LearningMaterial.objects.prefetch_related('goals').all()
    context = {
        'title': 'AIとともに学習するクイズアプリ',
        'materials': materials,
    }
    return render(request, 'learning/index.html', context)


def subject_select(request):
    """教科選択画面 (Math / English)"""
    return render(request, 'f2/subject_select.html')


def topic_list(request, subject):
    """トピック一覧画面（データベースからリアルタイム取得）"""
    materials = LearningMaterial.objects.filter(subject=subject).order_by('-last_used_at')

    TOTAL_SLOTS = 8  # 画面全体のカード枠数
    active_count = materials.count()
    
    empty_slots_count = max(0, TOTAL_SLOTS - 1 - active_count)
    subject_name = "Math" if subject == "math" else "English"

    context = {
        'subject': subject,
        'subject_name': subject_name,
        'topics': materials,
        'empty_slots': range(empty_slots_count),
    }
    return render(request, 'f2/topic_list.html', context)


def add_topic(request, subject):
    """「ファイルを追加」ボタンを押したときの処理"""
    # 1. 新しいトピックを作成
    new_topic = LearningMaterial.objects.create(
        subject=subject,
        title="no title",
        progress=0,
        last_used_at=timezone.now()
    )
    # 2. 🌟 作成したトピックのチャット画面へ直接移動！
    return redirect(f'/topic/{new_topic.id}/')


def topic_detail(request, topic_id):
    """トピック詳細・チャット画面"""
    material = get_object_or_404(LearningMaterial, id=topic_id)
    
    # アクセスした瞬間「最後に使った日」を更新
    material.last_used_at = timezone.now()
    material.save()
    
    # 🌟 テンプレートを chat.html に変更！
    return render(request, 'f2/chat.html', {'topic': material})


# リンクエラー防止用の仮ビュー
def ai_chat_start(request):
    return render(request, 'f2/subject_select.html')
    