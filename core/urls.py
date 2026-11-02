from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, reverse_lazy

from . import views

login_view = LoginView.as_view(
    template_name="core/login.html",
    redirect_authenticated_user=True,
    next_page=reverse_lazy("dashboard"),
)
urlpatterns = [
    path('', views.home, name='home'),
    path('login/', login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analise/', views.analizeForm, name='analize'),
    path('analise-form/', views.analizeForm, name='analizeForm'),
    path('analise/excluir/', views.excluir_analizes, name='excluirAnalizes'),
    path('historico/', views.historico, name='historico'),
    path('media/<path:caminho>', views.imagem_analise, name='imagem_analise'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)