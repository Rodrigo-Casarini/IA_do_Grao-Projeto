from django.conf import settings
from django.db import models
from django.utils import timezone


class Analize(models.Model):
    TIPO_GRAO_CHOICES = [
        ('feijao', 'Feijão'),
        ('milho', 'Milho'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_analise', 'Em análise'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ]

    SENSIBILIDADE_CHOICES = [
        ('sensivel', 'Sensível - a partir de 10%'),
        ('normal', 'Normal - a partir de 15%'),
        ('rigorosa', 'Rigorosa - a partir de 30%'),
    ]
    
    
    tipo_grao = models.CharField(max_length=20, choices=TIPO_GRAO_CHOICES)
    data_analise = models.DateField(default=timezone.now)
    sensibilidade = models.CharField(
        max_length=20,
        choices=SENSIBILIDADE_CHOICES,
        default='normal',
    )
    imagem_grao = models.ImageField(upload_to='analises/')
    imagem_grao_2 = models.ImageField(upload_to='analises/', blank=True, null=True)
    imagem_grao_3 = models.ImageField(upload_to='analises/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    observacao = models.TextField(blank=True, default='')
    observacao_usuario = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)
    resultado = models.TextField(blank=True, default="")
    confianca = models.FloatField(null=True, blank=True)
    detalhes = models.JSONField(default=list, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analises',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Análise'
        verbose_name_plural = 'Análises'

    def __str__(self):
        return f"Análise - {self.get_tipo_grao_display()} - {self.data_analise}"