from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db.models import Avg
from django.contrib.auth import login as auth_login
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AnalizeForm, CadastroForm
from .models import Analize
from .classificacoes import (
    classe_compativel,
    contar_classes_compativeis,
    contar_classes_incompativeis,
    contar_detalhe,
    contagens_detalhe,
    estado_classe,
    rotulo_classe,
)

from datetime import timedelta
import json
from django.utils import timezone
from django.conf import settings


def home(request):
    return render(request, 'core/index.html')


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.POST.get('next') or request.GET.get('next', '')
    form = CadastroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        auth_login(request, usuario)
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('dashboard')

    return render(request, 'core/cadastro.html', {
        'form': form,
        'next': next_url,
    })


@login_required(login_url='login')
def dashboard(request):
    analizes = Analize.objects.filter(usuario=request.user)
    total = analizes.count()
    feijao = analizes.filter(tipo_grao='feijao').count()
    milho = analizes.filter(tipo_grao='milho').count()
    aprovados = analizes.filter(status='aprovado').count()
    pendentes = analizes.filter(status='pendente').count()
    rejeitados = analizes.filter(status='rejeitado').count()
    confianca_media = analizes.aggregate(media=Avg('confianca'))['media']
    confianca_media_percentual = (
        confianca_media * 100 if confianca_media is not None else None
    )
    total_mofados = sum(
        sum(
            contar_detalhe(detalhe, "mofado", analise.tipo_grao)
            for detalhe in (analise.detalhes or [])
        )
        for analise in analizes
    )
    maior_risco = max(
        analizes,
        key=lambda analise: sum(
            contar_detalhe(detalhe, "mofado", analise.tipo_grao)
            for detalhe in (analise.detalhes or [])
        ),
        default=None,
    )
    ultima_rejeitada = analizes.filter(status='rejeitado').order_by('-created_at').first()
    recentes = analizes[:4]

    context = {
        'total': total,
        'feijao': feijao,
        'milho': milho,
        'aprovados': aprovados,
        'pendentes': pendentes,
        'rejeitados': rejeitados,
        'total_mofados': total_mofados,
        'confianca_media': confianca_media_percentual,
        'maior_risco': maior_risco,
        'ultima_rejeitada': ultima_rejeitada,
        'recentes': recentes,
    }
    return render(request, 'core/dashboard.html', context)


@login_required(login_url='login')
def analizeForm(request):
    if request.method == "POST":
        form = AnalizeForm(request.POST, request.FILES)

        if form.is_valid():
            analise = form.save(commit=False)
            analise.usuario = request.user
            analise.status = "pendente"
            analise.sensibilidade = form.cleaned_data.get("sensibilidade") or "normal"
            imagens = form.cleaned_data["imagens"]
            analise.imagem_grao.save(imagens[0].name, imagens[0], save=False)
            if len(imagens) > 1:
                analise.imagem_grao_2.save(imagens[1].name, imagens[1], save=False)
            if len(imagens) > 2:
                analise.imagem_grao_3.save(imagens[2].name, imagens[2], save=False)

            analise.save()

            from .detector import analisar_imagem

            imagens = [
                imagem for imagem in (
                    analise.imagem_grao,
                    analise.imagem_grao_2,
                    analise.imagem_grao_3,
                ) if imagem
            ]
            resultados = [
                analisar_imagem(imagem, analise.sensibilidade)
                for imagem in imagens
            ]

            detalhes = []
            mofados = 0
            saudaveis = 0
            incompatíveis = 0

            for indice, resultado in enumerate(resultados, start=1):
                contagens = resultado.get("contagens", {})
                mofados_imagem = contar_classes_compativeis(
                    contagens, "mofado", analise.tipo_grao
                )
                saudaveis_imagem = contar_classes_compativeis(
                    contagens, "saudavel", analise.tipo_grao
                )
                incompatíveis_imagem = contar_classes_incompativeis(
                    contagens, analise.tipo_grao
                )
                mofados += mofados_imagem
                saudaveis += saudaveis_imagem
                incompatíveis += incompatíveis_imagem
                deteccoes = [
                    {
                        **deteccao,
                        "compativel_tipo_grao": classe_compativel(
                            deteccao.get("classe", ""), analise.tipo_grao
                        ),
                    }
                    for deteccao in resultado["deteccoes"]
                ]

                detalhes.append({
                    "imagem": indice,
                    "quantidade": resultado["quantidade"],
                    "mofados": mofados_imagem,
                    "saudaveis": saudaveis_imagem,
                    "incompativeis": incompatíveis_imagem,
                    "texto": resultado["texto"],
                    "deteccoes": deteccoes,
                    "contagens": contagens,
                    "confianca": resultado["confianca"],
                    "confianca_media": resultado.get("confianca_media"),
                    "percentual_medio": resultado.get("percentual_medio"),
                    "sensibilidade": analise.sensibilidade,
                    "tipo_grao": analise.tipo_grao,
                    "largura": resultado.get("largura"),
                    "altura": resultado.get("altura"),
                })

            deteccoes_incompativeis = sorted({
                deteccao.get("classe", "")
                for resultado in resultados
                for deteccao in resultado["deteccoes"]
                if not classe_compativel(
                    deteccao.get("classe", ""), analise.tipo_grao
                )
            })
            tipo_grao_label = dict(Analize.TIPO_GRAO_CHOICES).get(
                analise.tipo_grao, analise.tipo_grao
            )
            classes_label = ", ".join(
                rotulo_classe(classe) for classe in deteccoes_incompativeis
            ) or "classes incompatíveis"
            aviso_incompatibilidade = ""
            if deteccoes_incompativeis:
                aviso_incompatibilidade = (
                    f" O modelo também detectou {classes_label}, incompatível "
                    f"com o tipo selecionado ({tipo_grao_label})."
                )

            if mofados > 0:
                analise.status = "rejeitado"
                analise.observacao = (
                    f"Rejeitado: foram identificados {mofados} grão(s) mofado(s)."
                ) + aviso_incompatibilidade
            elif incompatíveis > 0:
                analise.status = "em_analise"
                analise.observacao = (
                    f"Revisão necessária: o modelo detectou {classes_label}, "
                    f"incompatível com o tipo selecionado ({tipo_grao_label})."
                )
            elif saudaveis > 0:
                analise.status = "aprovado"
                analise.observacao = (
                    "Aprovado: somente grãos saudáveis foram identificados."
                ) + aviso_incompatibilidade
            else:
                analise.status = "rejeitado"
                analise.observacao = (
                    "Rejeitado: nenhum grão foi identificado."
                ) + aviso_incompatibilidade

            confiancas = [
                resultado["confianca"]
                for resultado in resultados
                if resultado["confianca"] is not None
            ]
            analise.resultado = f"{len(imagens)} imagem(ns) analisada(s)."
            analise.confianca = max(confiancas) if confiancas else None
            analise.detalhes = detalhes
            analise.save(update_fields=[
                "resultado",
                "confianca",
                "detalhes",
                "status",
                "observacao",
            ])

            return redirect("historico")

    else:
        form = AnalizeForm()

    return render(request, "core/analize.html", {"form": form})


def analize(request):
    return redirect('historico')


@login_required(login_url='login')
@require_POST
def excluir_analizes(request):
    ids = request.POST.getlist('analize_ids')
    analizes = Analize.objects.filter(usuario=request.user, id__in=ids)

    for analise in analizes:
        for imagem in (analise.imagem_grao, analise.imagem_grao_2, analise.imagem_grao_3):
            if imagem:
                imagem.delete(save=False)

    analizes.delete()
    return redirect('historico')


@login_required(login_url='login')
def historico(request):
    analizes = Analize.objects.filter(usuario=request.user).order_by('-created_at')
    tipo = request.GET.get('tipo_grao', '')
    status = request.GET.get('status', '')
    sensibilidade = request.GET.get('sensibilidade', '')
    data_inicio = request.GET.get('data_inicio', '')
    data_fim = request.GET.get('data_fim', '')
    dias = request.GET.get('dias', '')
    retenção_dias = getattr(settings, 'HISTORICO_EXCLUSAO_DIAS', 0)

    if retenção_dias > 0:
        analizes.filter(
            created_at__lt=timezone.now() - timedelta(days=retenção_dias)
        ).delete()

    if dias:
        try:
            dias_int = int(dias)
            analizes = analizes.filter(
                created_at__gte=timezone.now() - timedelta(days=dias_int)
            )
        except ValueError:
            pass

    if tipo:
        analizes = analizes.filter(tipo_grao=tipo)
    if status:
        analizes = analizes.filter(status=status)
    if sensibilidade:
        analizes = analizes.filter(sensibilidade=sensibilidade)
    if data_inicio:
        analizes = analizes.filter(data_analise__gte=data_inicio)
    if data_fim:
        analizes = analizes.filter(data_analise__lte=data_fim)

    for analise in analizes:
        detalhes_por_imagem = {
            detalhe.get('imagem'): detalhe
            for detalhe in (analise.detalhes or [])
        }
        for detalhe in (analise.detalhes or []):
            contagens = contagens_detalhe(detalhe)
            detalhe['classes_resumo'] = []
            for deteccao in detalhe.get('deteccoes', []):
                deteccao['classe_exibicao'] = rotulo_classe(
                    deteccao.get('classe', '')
                )
                deteccao['compativel_tipo_grao'] = classe_compativel(
                    deteccao.get('classe', ''), analise.tipo_grao
                )

            for nome, quantidade in contagens.items():
                compativel = classe_compativel(nome, analise.tipo_grao)
                detalhe['classes_resumo'].append({
                    'rotulo': rotulo_classe(nome),
                    'quantidade': quantidade,
                    'estado': (
                        estado_classe(nome) if compativel else 'incompativel'
                    ),
                })

        analise.imagens_visualizacao = []
        for indice, imagem in enumerate((
            analise.imagem_grao,
            analise.imagem_grao_2,
            analise.imagem_grao_3,
        ), start=1):
            if not imagem:
                continue

            detalhe = detalhes_por_imagem.get(indice, {})
            caixas = [
                {
                    **deteccao['caixa'],
                    'estado': (
                        estado_classe(deteccao.get('classe', ''))
                        if classe_compativel(
                            deteccao.get('classe', ''), analise.tipo_grao
                        )
                        else 'incompativel'
                    ),
                }
                for deteccao in detalhe.get('deteccoes', [])
                if deteccao.get('caixa')
            ]
            analise.imagens_visualizacao.append({
                'indice': indice,
                'url': imagem.url,
                'boxes_json': json.dumps({
                    'largura': detalhe.get('largura') or 1,
                    'altura': detalhe.get('altura') or 1,
                    'caixas': caixas,
                }),
            })

    context = {
        'analizes': analizes,
        'filtros': {
            'tipo_grao': tipo,
            'status': status,
            'sensibilidade': sensibilidade,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'dias': dias,
        },
        'tipo_choices': Analize.TIPO_GRAO_CHOICES,
        'status_choices': Analize.STATUS_CHOICES,
        'sensibilidade_choices': Analize.SENSIBILIDADE_CHOICES,
    }
    return render(request, 'core/historico.html', context)