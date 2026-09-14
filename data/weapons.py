""" Weapons database. """

# * EDITAVEL: adicione o nome da arma no mapa do personagem e o texto em MANUAL_WEAPONS.

_LOCAL_KIT_WEAPON_NAMES = {
    "xuanling": "Azure Oath", "lucy": "Spectral Trigger", "rebecca": "Skull Thrasher",
    "hiyuki": "Frostburn", "sigrika": "Solsworn Ciphers", "aemeath": "Everbright Polestar",
    "mornye": "Starfield Calibrator", "lynae": "Spectrum Blaster", "chisa": "Kumokiri",
    "galbrena": "Lux Umbra", "iuno": "Moongazer's Sigil", "augusta": "Thunderflare Dominion",
    "phrolova": "Lethean Elegy", "zani": "Blazing Justice", "ciaccona": "Woodland Aria",
    "cartethyia": "Defier's Thorn", "lupa": "Wildfire Mark", "cantarella": "Whispers of Sirens",
    "brant": "Unflickering Valor", "phoebe": "Luminous Hymn", "shorekeeper": "Stellar Symphony",
    "jingran": "Thousandfold Deliverance", "zhezhi": "Rime-Draped Sprouts", "changli": "Blazing Brilliance",
    "jiyan": "Verdant Summit", "jinhsi": "Ages of Harvest", "yinlin": "Stringmaster",
    "xiangliyao": "Verity's Handle", "luukherssen": "Signature Weapon",
    "aalto": "The Last Dance", "baizhi": "Stellar Symphony", "buling": "Stellar Symphony",
    "calcharo": "Lustrous Razor", "camellya": "Red Spring", "carlotta": "The Last Dance",
    "chixia": "The Last Dance", "danjin": "Blazing Brilliance", "encore": "Stringmaster",
    "jianxin": "Verity's Handle", "lingyang": "Abyss Surges", "lumi": "Lustrous Razor",
    "mortefi": "Static Mist", "qiuyuan": "Signature Weapon", "roccia": "Tragicomedy",
    "sanhua": "Emerald of Genesis", "taoqi": "Dauntless Evernight", "verina": "Stellar Symphony",
    "youhu": "Abyss Surges", "yuanwu": "Ages of Harvest", "yangyang": "Jianxin's Signature Weapon",
    "yangyang: xuanling": "Azure Oath", 
    "rover: spectro": "Emerald of Genesis",
    "rover: havoc": "Emerald of Genesis",
    "rover: aero": "Emerald of Genesis",
    "rover: electro": "Blazing Brilliance",
    "rover: glacio": "Emerald of Genesis",
    "hiuyki": "Frostburn",
}
# Manual weapon overrides. Add the verified PT-BR and EN text for each character ID.
MANUAL_WEAPONS: dict[str, dict[str, any]] = {
    "suisui": {
        "name": "Firstlight's Herald",
        "PT-BR": """ATQ BASE (NV. 90): 412
REGEN. DE ENERGIA: 76.9%

## PASSIVA
Coroa de Primavera

O HP Máx. aumenta em 12%. Ao ativar a Liberação da Ressonância, restaura 8 de Energia de Concerto a si mesmo, podendo ser ativado uma vez a cada 20s. Cada vez que aplicar a Esfoladura Criogênica, obtém Mácula de Neve por 6s; cada vez que causar Cura, obtém Marolas por 6s. Se o próprio Ressonante tiver aplicado a Esfoladura Criogênica e causado Cura enquanto estiver em campo, a próxima Habilidade Outro concederá os efeitos Mácula de Neve e Marolas por 6s. Quando o próprio Ressonante possuir Mácula de Neve e Marolas simultaneamente, o ATQ de todos os Ressonantes próximos na equipe aumenta em 20%. Efeitos de mesmo nome não se acumulam.""",
        "EN": """BASE ATK (LV. 90): 412
ENERGY REGEN: 76.9%

## PASSIVE
Crown of Spring

Max HP increases by 12%. When Resonance Liberation is activated, restores 8 Concerto Energy to the wielder, which can be triggered once every 20s. Each time Glacio Chafe is applied, gains Snow Taint for 6s; each time healing is dealt, gains Ripples for 6s. If the wielder applies Glacio Chafe and deals healing while on the field, the next Outro Skill grants Snow Taint and Ripples for 6s. When the wielder has both Snow Taint and Ripples, the ATK of nearby team Resonators increases by 20%. Effects with the same name do not stack.""",
    },
    "verina": {
        "name": "Variation",
        "PT-BR": """ATQ BASE (NV. 90): 412 
REGEN. DE ENERGIA: 77.0% 

## PASSIVA 
Ária Incessante

Ao lançar a Habilidade de Ressonância, restaura 8 de Energia de Concerto. Este efeito pode ser ativado 1 vez(es) a cada 20s.""",
        "EN": """BASE ATK (LV. 90): 412 
ENERGY REGEN: 76.9% 

## PASSIVE 
Ceaseless Aria

When Resonance Skill is cast, restore 8 Concerto Energy. This effect can be triggered 1 time(s) every 20s.""",
    },
}