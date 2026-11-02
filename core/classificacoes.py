from collections import Counter


ROTULOS_CLASSES = {
    "feijao_mofado": "Feijão mofado",
    "feijao_bom": "Feijão bom",
    "milho_mofado": "Milho mofado",
    "milho_bom": "Milho bom",
    "mofado": "Grão mofado",
}


def estado_classe(nome):
    sufixo = str(nome).strip().casefold().split("_")[-1]
    if sufixo == "mofado":
        return "mofado"
    if sufixo == "bom":
        return "saudavel"
    return "desconhecido"


def classe_e_mofada(nome):
    return estado_classe(nome) == "mofado"


def classe_compativel(nome, tipo_grao):
    familia = str(nome).strip().casefold().split("_", 1)[0]
    if familia in {"feijao", "milho"}:
        return familia == tipo_grao
    return True


def contar_classes(contagens, estado):
    return sum(
        int(quantidade)
        for nome, quantidade in contagens.items()
        if estado_classe(nome) == estado
    )


def contar_classes_compativeis(contagens, estado, tipo_grao):
    return sum(
        int(quantidade)
        for nome, quantidade in contagens.items()
        if classe_compativel(nome, tipo_grao)
        and estado_classe(nome) == estado
    )


def contar_classes_incompativeis(contagens, tipo_grao):
    return sum(
        int(quantidade)
        for nome, quantidade in contagens.items()
        if not classe_compativel(nome, tipo_grao)
    )


def rotulo_classe(nome):
    chave = str(nome).strip().casefold()
    return ROTULOS_CLASSES.get(
        chave,
        " ".join(parte.capitalize() for parte in chave.split("_")),
    )


def contagens_detalhe(detalhe):
    contagens = detalhe.get("contagens") or {}
    if contagens:
        return contagens
    return dict(Counter(
        deteccao.get("classe", "")
        for deteccao in detalhe.get("deteccoes", [])
    ))


def contar_detalhe(detalhe, estado, tipo_grao=None):
    contagens = contagens_detalhe(detalhe)
    if contagens:
        if tipo_grao:
            return contar_classes_compativeis(contagens, estado, tipo_grao)
        return contar_classes(contagens, estado)
    if estado == "mofado":
        return int(detalhe.get("mofados", 0))
    return 0