"""Verified character quotes used by the Tethys character banner."""

# * EDITAVEL: adicione uma tupla de frases para o mesmo ID usado nos catalogos de personagens.

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS

# Unknown characters stay blank until a quote is added for their approved ID.
CHARACTER_QUOTES: dict[str, tuple[str, ...]] = {
    # Jinzhou and core resonators
    "aalto": (
        "Dinheiro não compra felicidade, mas compra os recursos para garantir que ninguém precise sofrer desnecessariamente. Isso é apenas um bom negócio.",
    ),
    "baizhi": (
        "Um remédio calmo para um mundo em apuros.",
    ),
    "calcharo": (
        "Soltem os cães da guerra.",
    ),
    "changli": (
        "Quem é o pássaro na gaiola agora?",
    ),
    "chixia": (
        "Queimando através das provações com pura paixão!",
    ),
    "danjin": (
        "Um caminho carmesim cortado através da escuridão.",
    ),
    "encore": (
        "Uma ovelha, duas ovelhas, três... onde eu estava?",
    ),
    "jianxin": (
        "Purificar a mente e equilibrar os ventos.",
    ),
    "jiyan": (
        "O escudo que protege Jinzhou.",
    ),
    "yinlin": (
        "Um jogo perigoso jogado nas sombras.",
    ),
    "yangyang": (
        "O vento sussurra sobre coisas perdidas no tempo.",
    ),
    "lingyang": (
        "Danço ao ritmo das montanhas.",
    ),
    "sanhua": (
        "Uma lâmina silenciosa refletindo a neve.",
    ),
    "mortefi": (
        "Uma faísca que acende a fúria controlada.",
    ),
    "taoqi": (
        "Uma fortaleza intransponível de defesa.",
    ),
    "verina": (
        "Que o verde brote e a vida floresça.",
    ),
    "yuanwu": (
        "Firme como o trovão nas rochas.",
    ),
    "youhu": (
        "Curiosidades e relíquias do passado.",
    ),

    # Resonators and newer characters
    "aemeath": (
        "A Estrela que Viaja Longe.",
    ),
    "augusta": (
        "A soberania esculpida em lâminas de ferro.",
    ),
    "brant": (
        "Brant é o meu nome, capitão da Trupe dos Tolos!",
    ),
    "buling": (
        "Uma faísca alegre que ilumina o caminho.",
    ),
    "camellya": (
        "Alimentem minhas flores, enganadores de si mesmos!",
    ),
    "carlotta": (
        "A vitória me favorece!",
    ),
    "cartethyia": (
        "Com Glória Eu Cairei.",
    ),
    "chisa": (
        "A dança sutil das pétalas ao vento.",
    ),
    "ciaccona": (
        "Onde a melodia e o destino se encontram.",
    ),
    "denia": (
        "Os segredos guardados nas profundezas da terra.",
    ),
    "galbrena": (
        "O fogo que consome as sombras do passado.",
    ),
    "hiyuki": (
        "A chama eterna que desbrava a neve.",
    ),
    "iuno": (
        "Sob o manto dos céus e das estrelas.",
    ),
    "jinhsi": (
        "O fluxo do tempo nunca para, e as sementes do passado...",
    ),
    "jingran": (
        "A força bruta que abala os alicerces da terra.",
    ),
    "lucilla": (
        "A estrela guia dos navegantes perdidos.",
    ),
    "lucy": (
        "Um sorriso radiante em meio ao caos.",
    ),
    "luuk herssen": (
        "A rigidez da lei e a justiça inflexível.",
    ),
    "lynae": (
        "A luz pura que penetra a névoa.",
    ),
    "mornye": (
        "O crepúsculo que antecede a aurora.",
    ),
    "phrolova": (
        "Devaneios no Além Carmesim.",
    ),
    "phoebe": (
        "A fé que guia a ordem e o mistério.",
    ),
    "qiuyuan": (
        "O eco do vento nas montanhas ancestrais.",
    ),
    "qingxiao": (
        "Quebre todas as correntes.",
    ),
    "rebecca": (
        "A determinação implacável no campo de batalha.",
    ),
    "roccia": (
        "A rocha inabalável sob as marés do tempo.",
    ),
    "sigrika": (
        "O escudo indomável das terras congeladas.",
    ),
    "shorekeeper": (
        "Agora tenho certeza. Tem que ser o amor.",
    ),
    "suisui": (
        "A fluidez das águas que contornam qualquer obstáculo.",
    ),
    "xiangli yao": (
        "Reconfiguração de lógica e inovação.",
    ),
    "xuanling": (
        "A harmonia do vento e da natureza.",
    ),
    "yangyang xuanling": (
        "O vento sussurra sobre coisas perdidas no tempo.",
    ),
    "zani": (
        "A chama selvagem que queima em silêncio.",
    ),
    "zhezhi": (
        "Pintando a realidade com sonhos.",
    ),
    "cantarella": (
        "Harmonia nas sombras, beleza no caos.",
    ),
    "lumi": (
        "A luz que ilumina os caminhos da verdade.",
    ),
    "lupa": (
        "A chama selvagem que queima as correntes.",
    ),

    # Rover variants share the same character lines.
    "rover": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover aero": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover spectro": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover glacio": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover electro": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover fusion": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
    "rover havoc": (
        "Ninguém vai sussurrar!",
        "Você vai obedecer!",
        "Eu sou a tempestade.",
    ),
}

INVALID_QUOTE_IDS = set(CHARACTER_QUOTES) - KNOWN_CHARACTER_IDS
if INVALID_QUOTE_IDS:
    raise ValueError(f"Quote IDs are not present in KNOWN_CHARACTER_IDS: {INVALID_QUOTE_IDS}")
