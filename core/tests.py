from datetime import date
from io import BytesIO
import json
import sys
from types import ModuleType
from unittest.mock import patch
from uuid import uuid4

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Analize


def _imagem_teste(nome="grao.png"):
    arquivo = BytesIO()
    Image.new("RGB", (2, 2), color="white").save(arquivo, format="PNG")
    return SimpleUploadedFile(
        nome,
        arquivo.getvalue(),
        content_type="image/png",
    )

class AnaliseTeste(TestCase):
    def criar_analise(self, tipo_grao, usuario=None):
        return Analize.objects.create(
            tipo_grao=tipo_grao,
            data_analise=date.today(),
            sensibilidade="normal",
            imagem_grao=_imagem_teste(),
            usuario=usuario,
        )

    def simular_detector(self, resultado):
        modulo = ModuleType("core.detector")
        modulo.analisar_imagem = lambda imagem, sensibilidade: resultado
        return patch.dict(sys.modules, {"core.detector": modulo})

    def autenticar(self):
        usuario = get_user_model().objects.create_user(
            username=f"teste-analise-{uuid4().hex}",
            password="senha-de-teste",
        )
        self.client.force_login(usuario)
        return usuario

    def test_cria_analise(self):
        analise = Analize.objects.create(
            tipo_grao="feijao",
            data_analise=date(2026, 2, 24),
            sensibilidade="normal",
            imagem_grao=_imagem_teste(),
            observacao_usuario="Teste 1",
        )

        self.assertEqual(analise.tipo_grao, "feijao")
        self.assertEqual(analise.observacao_usuario, "Teste 1")
        self.assertIsNotNone(analise.created_at)

    def test_pagina_inicial_continua_publica(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/index.html")
        self.assertContains(response, "Entrar")

    def test_login_valido_redireciona_para_dashboard(self):
        usuario = get_user_model().objects.create_user(
            username="teste-login",
            password="senha-de-teste",
        )

        response = self.client.post(
            reverse("login"),
            {"username": usuario.username, "password": "senha-de-teste"},
        )

        self.assertRedirects(response, reverse("dashboard"))

    def test_cadastro_cria_conta_autentica_e_preserva_destino(self):
        username = f"novo-usuario-{uuid4().hex[:8]}"
        senha = f"Cadastro!{uuid4().hex[:12]}"
        destino = reverse("analizeForm")
        pagina_cadastro = self.client.get(reverse("cadastro"))

        self.assertTemplateUsed(pagina_cadastro, "core/cadastro.html")
        self.assertContains(pagina_cadastro, "Nome de usuário")

        response = self.client.post(
            f"{reverse('cadastro')}?next={destino}",
            {
                "username": username,
                "password1": senha,
                "password2": senha,
                "next": destino,
            },
        )

        self.assertRedirects(response, destino)
        usuario = get_user_model().objects.get(username=username)
        self.assertTrue(usuario.check_password(senha))
        self.assertEqual(
            self.client.get(destino).status_code,
            200,
        )

    def test_login_redireciona_para_analise_solicitada(self):
        usuario = get_user_model().objects.create_user(
            username="teste-login-analise",
            password="senha-de-teste",
        )
        resposta_protegida = self.client.get(reverse("analizeForm"))
        self.assertRedirects(
            resposta_protegida,
            f"{reverse('login')}?next={reverse('analizeForm')}",
        )

        response = self.client.post(
            resposta_protegida.url,
            {"username": usuario.username, "password": "senha-de-teste"},
        )

        self.assertRedirects(response, reverse("analizeForm"))

    def test_usuario_autenticado_ve_botao_sair_na_landing(self):
        usuario = get_user_model().objects.create_user(
            username="teste-ja-logado",
            password="senha-de-teste",
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sair")

    def test_sidebar_sauda_usuario_pelo_primeiro_nome(self):
        usuario = get_user_model().objects.create_user(
            username=f"teste-saudacao-{uuid4().hex}",
            first_name="Marina",
            password="senha-de-teste",
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Olá,")
        self.assertContains(response, "Marina")

    def test_dashboard_e_historico_mostram_apenas_analises_do_usuario(self):
        usuario = self.autenticar()
        outro_usuario = get_user_model().objects.create_user(
            username=f"outro-usuario-{uuid4().hex}",
            password="senha-de-teste",
        )
        propria = self.criar_analise("feijao", usuario=usuario)
        alheia = self.criar_analise("milho", usuario=outro_usuario)
        antiga_sem_dono = self.criar_analise("milho")

        dashboard = self.client.get(reverse("dashboard"))
        historico = self.client.get(reverse("historico"))

        self.assertEqual(dashboard.context["total"], 1)
        self.assertEqual(
            [analise.id for analise in dashboard.context["recentes"]],
            [propria.id],
        )
        self.assertContains(historico, f"#{propria.id}")
        self.assertNotContains(historico, f"#{alheia.id}")
        self.assertNotContains(historico, f"#{antiga_sem_dono.id}")

    def test_dashboard_historico_e_exclusao_exigem_login(self):
        for nome in ("dashboard", "historico"):
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertRedirects(
                    resposta,
                    f"{reverse('login')}?next={reverse(nome)}",
                )

        resposta = self.client.post(reverse("excluirAnalizes"), {})
        self.assertRedirects(
            resposta,
            f"{reverse('login')}?next={reverse('excluirAnalizes')}",
        )

    def test_sair_redireciona_para_landing_publica(self):
        usuario = get_user_model().objects.create_user(
            username="teste-logout",
            password="senha-de-teste",
        )
        self.client.force_login(usuario)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("home"))

    def test_exclui_apenas_as_analises_selecionadas(self):
        usuario = self.autenticar()
        outro_usuario = get_user_model().objects.create_user(
            username=f"outro-usuario-{uuid4().hex}",
            password="senha-de-teste",
        )
        selecionada = self.criar_analise("feijao", usuario=usuario)
        mantida = self.criar_analise("milho", usuario=usuario)
        alheia = self.criar_analise("milho", usuario=outro_usuario)

        response = self.client.post(
            reverse("excluirAnalizes"),
            {"analize_ids": [selecionada.id, alheia.id]},
        )

        self.assertRedirects(response, reverse("historico"))
        self.assertFalse(Analize.objects.filter(id=selecionada.id).exists())
        self.assertTrue(Analize.objects.filter(id=mantida.id).exists())
        self.assertTrue(Analize.objects.filter(id=alheia.id).exists())

    def test_observacoes_automatica_e_do_usuario_ficam_separadas(self):
        usuario = self.autenticar()
        observacao = "Amostra do lote 42, armazenada em local úmido."
        resultado = {
            "quantidade": 2,
            "texto": "milho_mofado (90.0%); milho_bom (85.0%)",
            "deteccoes": [
                {"classe": "milho_mofado", "confianca": 0.9, "percentual": 90},
                {"classe": "milho_bom", "confianca": 0.85, "percentual": 85},
            ],
            "contagens": {"milho_mofado": 1, "milho_bom": 1},
            "confianca": 0.9,
        }

        with self.simular_detector(resultado):
            response = self.client.post(
                reverse("analizeForm"),
                {
                    "tipo_grao": "milho",
                    "data_analise": "2026-10-01",
                    "observacao_usuario": observacao,
                    "sensibilidade": "normal",
                    "imagens": _imagem_teste(),
                },
            )

        self.assertRedirects(response, reverse("historico"))
        analise = Analize.objects.get()
        self.assertEqual(analise.observacao_usuario, observacao)
        self.assertEqual(
            analise.observacao,
            "Rejeitado: foram identificados 1 grão(s) mofado(s).",
        )
        self.assertEqual(analise.status, "rejeitado")
        self.assertEqual(analise.detalhes[0]["mofados"], 1)
        self.assertEqual(analise.detalhes[0]["saudaveis"], 1)
        self.assertEqual(analise.usuario, usuario)
