#!/usr/bin/env python3
"""Pinterest-specific content strategy for Anthares literary/writing clips."""
import re
from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class PinterestStrategy:
    bucket: str
    weight: float
    board: str
    title: str
    description: str
    topics: tuple[str, ...]


RULES = (
    (
        "characters",
        ("personagem", "personagens", "protagonista", "antagonista", "arco", "motivação", "motivacao"),
        "Construção de personagens",
        ("escrita criativa", "personagens", "criação de personagens", "ficção", "storytelling"),
        "education",
        0.70,
    ),
    (
        "worldbuilding",
        ("fantasia", "worldbuilding", "mundo", "magia", "lore", "universo", "ambientação", "ambientacao"),
        "Fantasia e worldbuilding",
        ("worldbuilding", "fantasia", "escrita criativa", "criação de mundos", "ficção"),
        "education",
        0.70,
    ),
    (
        "classics",
        ("púchkin", "puchkin", "longino", "clássico", "classico", "literatura clássica", "literatura classica"),
        "Literatura clássica",
        ("literatura clássica", "livros", "leitura", "análise literária", "autores clássicos"),
        "literature",
        0.15,
    ),
    (
        "challenges",
        ("desafio", "prompt", "exercício", "exercicio", "proposta de escrita"),
        "Desafios de escrita",
        ("desafio de escrita", "prompt de escrita", "exercício de escrita", "escrita criativa"),
        "education",
        0.70,
    ),
    (
        "anthares",
        ("anthares", "conto", "contos", "leitor beta", "avaliação de texto", "avaliacao de texto", "publicar conto"),
        "Contos Anthares",
        ("contos", "escritores", "leitura", "escrita criativa", "comunidade de escritores"),
        "anthares",
        0.10,
    ),
    (
        "authors",
        ("autor", "autora", "livro", "livros", "romance", "obra", "obras"),
        "Livros e autores",
        ("livros", "autores", "literatura", "leitura", "escrita"),
        "literature",
        0.15,
    ),
    (
        "quotes",
        ("frase", "trecho", "citação", "citacao"),
        "Frases e trechos literários",
        ("frases literárias", "trechos de livros", "literatura", "leitura"),
        "literature",
        0.15,
    ),
    (
        "mistakes",
        ("erro", "erros", "clichê", "cliche", "vício", "vicio", "evite", "não faça", "nao faca"),
        "Erros de escritores",
        ("erros de escrita", "dicas de escrita", "escritores", "escrita criativa"),
        "education",
        0.70,
    ),
    (
        "technique",
        ("diálogo", "dialogo", "descrição", "descricao", "ponto de vista", "pov", "conflito", "estrutura", "narrador", "cena"),
        "Técnicas de escrita",
        ("técnicas de escrita", "escrita criativa", "ficção", "storytelling", "dicas de escrita"),
        "education",
        0.70,
    ),
)

DEFAULT = (
    "writing",
    "Como escrever melhor",
    ("como escrever", "escrita criativa", "dicas de escrita", "escritores", "ficção"),
    "education",
    0.70,
)


def _clean(text):
    text = re.sub(r"https?://\S+", "", str(text or ""))
    text = re.sub(r"(^|\s)#[\wÀ-ÿ_-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _truncate(text, limit):
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[: limit + 1].rsplit(" ", 1)[0].rstrip(" ,;:.-")
    return (cut or text[:limit]).strip()


def classify(text):
    folded = _clean(text).casefold()
    for name, needles, board, topics, bucket, weight in RULES:
        if any(n.casefold() in folded for n in needles):
            return name, board, topics, bucket, weight
    return DEFAULT


def build_title(caption, explicit_title="", category="writing"):
    if _clean(explicit_title):
        return _truncate(explicit_title, 100)
    base = _clean(caption).split("\n", 1)[0]
    if not base:
        base = "Dicas de escrita criativa"
    first = re.split(r"(?<=[.!?])\s+", base, maxsplit=1)[0].strip(" .")
    lower = first.casefold()
    if lower.startswith(("como ", "por que ", "quando ", "onde ", "o que ", "qual ", "quais ")):
        title = first
    elif category == "characters":
        title = f"Como construir personagens: {first}"
    elif category == "worldbuilding":
        title = f"Worldbuilding para escritores: {first}"
    elif category == "mistakes":
        title = f"Erros de escrita: {first}"
    elif category == "classics":
        title = f"Literatura clássica: {first}"
    else:
        title = f"Dica de escrita: {first}"
    return _truncate(title, 100)


def build_description(caption, board, topics, explicit_description=""):
    if _clean(explicit_description):
        return _truncate(explicit_description, 800)
    base = _truncate(caption, 590)
    semantic = ", ".join(topics[:5])
    suffix = f" Conteúdo sobre {semantic}. Salve na pasta {board} para consultar depois."
    return _truncate((base + suffix).strip(), 800)


def build_strategy(caption, title="", description="", board=""):
    category, auto_board, topics, bucket, weight = classify(" ".join((title, caption, description)))
    final_board = _truncate(board, 180) if _clean(board) else auto_board
    final_title = build_title(caption, title, category)
    final_description = build_description(caption, final_board, topics, description)
    return PinterestStrategy(
        bucket=bucket,
        weight=weight,
        board=final_board,
        title=final_title,
        description=final_description,
        topics=tuple(topics[:10]),
    )


def strategy_dict(*args, **kwargs):
    return asdict(build_strategy(*args, **kwargs))
