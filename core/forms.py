from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Analize


class CadastroForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nome de usuário"
        self.fields["password1"].label = "Senha"
        self.fields["password1"].help_text = (
            "Use pelo menos 8 caracteres e evite senhas comuns ou apenas numéricas."
        )
        self.fields["password2"].label = "Confirme a senha"
        self.fields["password2"].help_text = "Digite a mesma senha novamente."


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [file for file in files if file]

        if len(files) > 3:
            raise forms.ValidationError("Selecione no máximo 3 imagens.")

        if not files:
            if self.required:
                raise forms.ValidationError("Adicione pelo menos uma imagem.")
            return []

        return [super().clean(file, initial) for file in files]


class AnalizeForm(forms.ModelForm):
    observacao_usuario = forms.CharField(
        label="Observação de quem realizou a análise",
        required=False,
        help_text="Registre informações da amostra, como lote, umidade ou armazenamento.",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Anotações sobre a amostra...",
        }),
    )
    imagens = MultipleImageField(
        label="Imagens da análise (até 3)",
        required=True,
        widget=MultipleImageInput(attrs={
            "class": "input-field file-input",
            "accept": "image/*",
            "multiple": True,
        }),
    )
    sensibilidade = forms.ChoiceField(
        label="Sensibilidade da análise",
        choices=Analize.SENSIBILIDADE_CHOICES,
        required=False,
        initial="normal",
        help_text="O percentual indica a confiança mínima para uma detecção. A confiança final é calculada automaticamente pela IA.",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Analize
        fields = ["tipo_grao", "data_analise", "observacao_usuario"]
        widgets = {
            "data_analise": forms.DateInput(attrs={"type": "date"}),
        }
        error_messages = {
            "tipo_grao": {
                "required": "Selecione o tipo de grão antes de continuar.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.order_fields([
            "tipo_grao",
            "data_analise",
            "imagens",
            "sensibilidade",
            "observacao_usuario",
        ])
        for name, field in self.fields.items():
            if name == "imagens":
                continue
            field.widget.attrs.update({"class": "input-field"})

            
            
            