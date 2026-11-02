from pathlib import Path
from collections import Counter

from django.conf import settings
import torch
from torchvision.ops import batched_nms
from ultralytics import YOLO

MODEL_PATHS = (
    settings.BASE_DIR / "treinamento" / "runs" / "detect" / "train-6" / "weights" / "best.pt",
    settings.BASE_DIR / "treinamento" / "runs" / "detect" / "train-8" / "weights" / "best.pt",
    settings.BASE_DIR / "treinamento" / "runs" / "detect" / "train-3" / "weights" / "best.pt",
)

SENSITIVITY_THRESHOLDS = {
    "sensivel": 0.10,
    "normal": 0.15,
    "rigorosa": 0.30,
}
NMS_IOU_THRESHOLD = 0.5


models = [YOLO(model_path) for model_path in MODEL_PATHS]
if models[0].names != models[1].names or models[0].names != models[2].names:
    raise ValueError("Os modelos train-6, train-8 e train-3 precisam ter as mesmas classes.")


def analisar_imagem(imagem, sensibilidade="normal"):
    caminho = Path(imagem.path)
    confidence_threshold = SENSITIVITY_THRESHOLDS.get(sensibilidade, 0.15)

    resultados = [
        modelo(
            str(caminho),
            conf=confidence_threshold,
            device=0,
            verbose=False,
        )[0]
        for modelo in models
    ]
    altura, largura = resultados[0].orig_shape

    caixas = []
    confiancas = []
    classes = []

    for resultado in resultados:
        for caixa in resultado.boxes:
            caixas.append(caixa.xyxy[0])
            confiancas.append(caixa.conf[0])
            classes.append(caixa.cls[0])

    deteccoes = []
    if caixas:
        caixas_tensor = torch.stack(caixas)
        confiancas_tensor = torch.stack(confiancas)
        classes_tensor = torch.stack(classes).to(dtype=torch.int64)
        indices = batched_nms(
            caixas_tensor,
            confiancas_tensor,
            classes_tensor,
            NMS_IOU_THRESHOLD,
        )

        for indice in indices:
            indice = int(indice)
            classe_id = int(classes_tensor[indice])
            confianca = float(confiancas_tensor[indice])
            x1, y1, x2, y2 = (
                round(float(coordenada), 2)
                for coordenada in caixas_tensor[indice].tolist()
            )
            deteccoes.append({
                "classe": resultados[0].names[classe_id],
                "confianca": round(confianca, 4),
                "percentual": round(confianca * 100, 2),
                "caixa": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            })

    if not deteccoes:
        return {
            "texto": "Nenhum grão foi detectado.",
            "quantidade": 0,
            "deteccoes": [],
            "confianca": None,
            "largura": largura,
            "altura": altura,
        }

    maior_confianca = max(item["confianca"] for item in deteccoes)
    confianca_media = sum(item["confianca"] for item in deteccoes) / len(deteccoes)
    contagens = dict(Counter(item["classe"] for item in deteccoes))
    texto = "; ".join(
        f"{item['classe']} ({item['confianca']:.1%})"
        for item in deteccoes
    )

    return {
        "texto": texto,
        "quantidade": len(deteccoes),
        "deteccoes": deteccoes,
        "contagens": contagens,
        "confianca": maior_confianca,
        "confianca_media": round(confianca_media, 4),
        "percentual_medio": round(confianca_media * 100, 2),
        "largura": largura,
        "altura": altura,
    }