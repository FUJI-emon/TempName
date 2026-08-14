from django.shortcuts import render
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

# views.py の末尾に追記

def finaltest(request):
    # templates/learning/ フォルダの中の finaltest.html を表示する
    return render(request, 'learning/finaltest.html')