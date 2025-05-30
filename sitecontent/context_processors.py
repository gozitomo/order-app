from .models import HeroContent

def hero_content(request):
    return {
        'hero': HeroContent.objects.first()
    }