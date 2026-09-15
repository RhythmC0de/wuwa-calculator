"""Character kits database."""

# * EDITAVEL: cada chave recebe skills, buffs e marcadores exibidos na tela.
# ? Se um kit nao existir, a interface usa o fallback manual quando disponivel.

# Manual kit overrides. Add or edit one entry per normalized character ID.
# Keep each skill in this shape: name, icon (URL or local path), description.


CHARACTER_KITS_DB: dict[str, dict[str, object]] = {
    "suisui": {
        "weapon_name": "Firstlight's Herald",
        "weapon_passive": "ATK +20% (R1 -> 40% at R5). While the wielder has both Snow Taint and Ripples active.",
        "skills": [
            {"name": "Basic Attack",
                "description": "Performs a series of attacks and builds the resources used by SuiSui's Stances."},
            {"name": "Resonance Skill",
                "description": "Switches stance and builds Cloud Breath or Floral Epistle according to the current state."},
            {"name": "Forte Circuit", "description": "Cloud Breath builds from Zephyr attacks. At 120, Awakening Spring becomes castable and resets Floral Epistle."},
            {"name": "Resonance Liberation",
                "description": "Consumes the available resource to enter the empowered stance and enables the next rotation sequence."},
            {"name": "Intro / Outro",
                "description": "Applies the active team effect and transfers the appropriate stance-based buff."},
        ],
    },
    "lucilla": {
        "weapon_name": "Freeze Frame",
        "weapon_passive": "Crit Rate +24.3%. ATK +12% (R1 -> 24% at R5). Glacio DMG Bonus +30% (R1 -> 60% at R5) after applying Glacio Chafe.",
        "skills": [
            {"name": "Basic Attack",
                "description": "Performs Normal Mode attacks that build Trace and interact with Photos."},
            {"name": "Resonance Skill",
                "description": "Spotlight applies the active Resonance Mode effect and advances Lucilla's resource state."},
            {"name": "Forte Circuit", "description": "Trace builds from Normal Mode attacks. Every 50 Trace converts into 1 Photo, up to 3 Photos."},
            {"name": "Resonance Liberation",
                "description": "Clear As Day becomes castable at 3 Photos and switches Lucilla to Reminiscence Mode."},
            {"name": "Intro / Outro", "description": "Applies or transfers Glacio Chafe effects and enables the incoming Resonator's rotation."},
        ],
    },
    "denia": {
        "weapon_name": "Forged Dwarf Star",
        "weapon_passive": "Increases the wielder's ATK and grants an additional effect after using a Resonance Skill.",
        "skills": [
            {"name": "Basic Attack",
                "description": "Performs a sequence of standard attacks."},
            {"name": "Resonance Skill",
                "description": "Deals the character's elemental damage and activates the current kit state."},
            {"name": "Forte Circuit",
                "description": "Consumes and builds the character's Forte resource to enhance the next ability."},
            {"name": "Resonance Liberation",
                "description": "Unleashes the character's ultimate attack and applies its associated state."},
            {"name": "Intro / Outro",
                "description": "Triggers the character's entry or team-support effect."},
        ],
    },
    "qingxiao": {
        "weapon_name": "Glint of Clouds",
        "weapon_passive": "Increases the wielder's ATK and strengthens the equipped character's signature rotation effects.",
        "skills": [
            {"name": "Basic Attack",
                "description": "Performs the character's basic attack sequence."},
            {"name": "Resonance Skill",
                "description": "Activates the character's primary skill effect."},
            {"name": "Forte Circuit",
                "description": "Uses Forte resources to enhance the character's special attacks."},
            {"name": "Resonance Liberation",
                "description": "Deals the character's ultimate damage and applies the associated state."},
            {"name": "Intro / Outro",
                "description": "Activates the character's entry and team transition effects."},
        ],
    },
}

MANUAL_CHARACTER_KITS: dict[str, dict[str, object]] = {
    "aalto": {
        "kit_name": "Aalto",
        "skills": [
            {"name": "Ataque Básico (Half Truths)", "description": "Basic Attack Aalto fires up to 5 consecutive shots, dealing Aero DMG. Basic Attack 4 will spread the Mist forward, which lasts for 1.5s."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "aemeath": {
        "kit_name": "Aemeath",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "augusta": {
    "kit_name": "Augusta",
    "skills": [
        {
            "name": "Ataque Básico - Caminho da Caçadora",
            "description": (
                "• Combo Básico: Até 4 golpes consecutivos de Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
                "• ATQ Pesado (Choque de Aço): Consome <font color='#eab308'><b>Vigor</b></font> para Dano <font color='#a855f7'><b>Voltaico</b></font>. "
                "Pressione ATQ Básico para emendar no 2º estágio.<br>"
                "• ATQ Aéreo & Esquiva: Consome <font color='#eab308'><b>Vigor</b></font> para Ataque em Mergulho. "
                "Contra-Ataque pós-esquiva causa Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
                "• <font color='#a855f7'><b>Proeza Cheia (100pt)</b></font>: Converte o Pesado em <font color='#6feaff'><b>Trovão Rugidor: Recuo</b></font>, "
                "encadeando em <font color='#6feaff'><b>Corte Giratório</b></font> (ATQ) ou <font color='#6feaff'><b>Uppercut</b></font> (Pulo).<br>"
                "• Modificador de Estado: Com Proeza/Ascendência cheia, altera os Contra-Ataques de Esquiva."
            )
        },
        {
            "name": "Habilidade de Ressonância: Lâmina da Guerreira",
            "description": """Augusta salta e golpeia o chão com seu espadão, causando Dano Voltaico.

    Contra-ATQ Evasivo: Luz Solar Eterna - Golpe

    Quando Ascendência está cheia, após uma Esquiva no chão, pressionar Habilidade de Ressonância realiza Contra-ATQ Evasivo: Luz Solar Eterna - Golpe, causando Dano Voltaico, considerado como Dano de Habilidade de Ressonância. Após uma Esquiva Aérea, pressionar ATQ Básico ou Habilidade de Ressonância realiza este mesmo ataque.

    Durante a ação, pressionar ATQ Básico ou Habilidade de Ressonância realiza Habilidade de Ressonância: Luz Solar Imortal - Salto.

    Se a Habilidade de Ressonância: Luz Solar Imortal - Salto for interrompida, ela pode ser realizada novamente após um certo período."""
        },
        {
            "name": "Circuito Forte - Invoca-me pelo Sol",
            "description": """Habilidade de Ressonância: Luz Solar Imortal - Golpe

    Quando Ascendência está cheia, Habilidade de Ressonância: Lâmina do Guerreiro é substituída por Habilidade de Ressonância: Luz Solar Imortal - Golpe, causando Dano Voltaico.

    Durante a ação, pressionar ATQ Básico ou Habilidade de Ressonância realiza Habilidade de Ressonância: Luz Solar Imortal - Salto.

    Se a Habilidade de Ressonância: Luz Solar Imortal - Golpe for interrompida, ela pode ser realizada novamente logo.

    Se a Habilidade de Ressonância: Luz Solar Imortal - Salto for interrompida, ela pode ser realizada novamente após um certo período.

    Pode ser realizada no ar.

    Habilidade de Ressonância: Luz Solar Imortal - Salto

    Causa Dano Voltaico.

    Durante a ação, pressionar ATQ Básico ou Habilidade de Ressonância realiza Habilidade de Ressonância: Luz Solar Imortal - Mergulho.

    Se a Habilidade de Ressonância: Luz Solar Imortal - Salto for interrompida, ela pode ser realizada novamente logo.

    Se a Habilidade de Ressonância: Luz Solar Imortal - Mergulho for interrompida, ela pode ser realizada novamente após um certo período.

    Só pode ser realizada no ar.

    Habilidade de Ressonância: Luz Solar Imortal - Mergulho

    Consome toda Ascendência para lançar esta habilidade, causando Dano Voltaico, considerado como Dano de ATQ Pesado.

    Realizar esta habilidade ganha 1 acúmulo de Majestade.

    Só pode ser realizada no ar.

    Ascendência

    Augusta pode acumular até 100 pontos de Ascendência.

    Ganha Ascendência ao causar dano com ATQ Normal.

    Ganha 20% de Ascendência ao realizar Habilidade Intro: Passo da Chama Dourada.

    Ganha e restaura 10% de Ascendência ao realizar Habilidade de Ressonância: Lâmina do Guerreiro.

    Ganha 40% de Ascendência ao realizar Liberação de Ressonância: Espada do Juramento Eterno."""
        },
        {
            "name": "Liberação de Ressonância - Conquista em Direção ao Sol",
            "description": """Liberação de Ressonância: Espada do Juramento Eterno

    Pressionar e soltar Liberação de Ressonância realiza esta habilidade. Augusta varre seu Espadão para frente, causando Dano Voltaico, considerado como Dano de ATQ Pesado.

    Liberação de Ressonância: Sublime é o Sol

    Quando Majestade alcança 2 acúmulos, segurar Liberação de Ressonância realiza Liberação de Ressonância: Sublime é o Sol. Realizar Liberação de Ressonância: Sublime é o Sol não consome Energia de Ressonância, mas 2 acúmulos de Majestade.

    Ao realizar Liberação de Ressonância: Sublime é o Sol, Augusta gera o Reino do Governante e entra no estado Juramento de Lealdade por 7s. Durante esse período, o tempo é temporariamente parado e a troca de Ressonante é bloqueada. Apenas Sublime é o Sol: Solisnato, Sublime é o Sol: Protetor Semprebrilho e Esquiva podem ser executados no estado Lealdade Jurada. O ATQ Aéreo pode ser realizado no ar.

    No estado Lealdade Jurada, pressionar ou segurar ATQ Básico realiza Sublime é o Sol: Solisnato. Augusta pode caminhar sobre a água sem consumir VIG neste estado.

    Realizar qualquer interação não relacionada ao combate termina Lealdade Jurada sem ativar Sublime é o Sol: Protetor Semprebrilho.

    Sublime é o Sol: Solisnato

    Causa Dano Voltaico, considerado como Dano de ATQ Pesado. Após realizar 9 vezes de Sublime é o Sol: Solisnato, pressionar ATQ Básico ou Liberação de Ressonância executa Sublime é o Sol: Protetor Semprebrilho.

    Sublime é o Sol: Protetor Semprebrilho

    Causa Dano Voltaico, considerado como Dano de ATQ Pesado. Realizar Sublime é o Sol: Protetor Semprebrilho termina o estado Juramento de Lealdade e consome todos os acúmulos de Coroa de Vontades posteriormente. Todos os outros Ressonantes da equipe serão forçados a sair de campo.

    Quando Lealdade Jurada termina, Sublime é o Sol: Protetor Semprebrilho é automaticamente realizado.

    Durante Lealdade Jurada, segurar Liberação de Ressonância pode realizar Sublime é o Sol: Protetor Semprebrilho antecipadamente.

    Reino da Governante

    Reino da Governante dura 30s.

    Quando Ressonantes da equipe realizam Habilidade Intro dentro do Reino da Governante, eles ganham um escudo igual a 650 + 5% do HP Máx. de Augusta por 10s. Este efeito não é acumulável. Este escudo não é transferido ao trocar de Ressonante.

    Majestade

    Augusta pode manter até 2 acúmulos de Majestade.

    Ganha 1 acúmulo de Majestade ao realizar Habilidade de Ressonância: Luz Solar Imortal - Mergulho.

    Ganha 1 acúmulo de Majestade quando outros Ressonantes da equipe realizam Habilidade Outro sob o efeito da Habilidade Outro: Canto de Batalha dos Inflexíveis de Augusta.

    """
        },
        {
            "name": "Habilidade Intro - Passo da Chama Dourada",
            "description": """Causa Dano Voltaico."""
        },
        {
            "name": "Habilidade Outro - Canção de Batalha dos Inflexíveis",
            "description": """O próximo Ressonante a entrar em campo ganha os seguintes efeitos por 14s. Os efeitos terminam imediatamente se ele for substituído.

Amplifica todo o Dano em 15%.

Ao realizar Habilidade Outro, Augusta ganha 1 acúmulo de Majestade e 1 acúmulo de Coroa de Vontades.

Coroa de Vontades

Cada acúmulo aumenta 15% de Dano Voltaico, até 1 acúmulo. Quando a Liberação de Ressonância: Sublime é o Sol: Guardião da Luz Perpétua termina, todos os acúmulos de Coroa de Vontades são removidos."""
        },
        {
            "name": "Habilidade Inata 1 - Favor da Glória",
            "description": """Quando Augusta causa dano, ela ganha um escudo igual a 350 + 2.5% de seu HP Máx. por 5s, ativado uma vez a cada 0.5s. Este efeito não é acumulável. Este escudo não é transferido ao trocar de Ressonante."""
        },
        {
            "name": "Habilidade Inata 2 - Bravura Calcinante",
            "description": """Quando Augusta está fora de combate por mais de 4s, ela ganha os seguintes efeitos, que podem ser ativados uma vez a cada 4s.

Se Majestade for menor que 1 acúmulo, restaura 1 acúmulo.

Restaura completamente Coroa de Vontades."""
        }
    ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "baizhi": {
        "kit_name": "Baizhi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "brant": {
        "kit_name": "Brant",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "buling": {
        "kit_name": "Buling",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "calcharo": {
        "kit_name": "Calcharo",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "camellya": {
        "kit_name": "Camellya",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "cantarella": {
        "kit_name": "Cantarella",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "carlotta": {
        "kit_name": "Carlotta",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "cartethyia": {
        "kit_name": "Cartethyia",
        "skills": [
            {"name": "Ataque Básico: Nome da Habilidade", "description": "Insira aqui a descrição detalhada do ataque básico da Cartethyia."},
            {"name": "Habilidade de Ressonância", "description": "Insira aqui a descrição detalhada da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Insira aqui a descrição detalhada do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Insira aqui a descrição detalhada da liberação de ressonância (Ult)."},
        ],
        "team_buffs": [("Bônus de Ataque em Equipe", 15.0)],
        "personal_buffs": [("Bônus de Dano Pessoal", 20.0)],
        "markers": [("Acumuladores / Stacks", 1.0)],
    },
    "changli": {
        "kit_name": "Changli",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "chisa": {
        "kit_name": "Chisa",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "chixia": {
        "kit_name": "Chixia",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "ciaccona": {
        "kit_name": "Ciaccona",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "danjin": {
        "kit_name": "Danjin",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "denia": {
        "kit_name": "Denia",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "encore": {
        "kit_name": "Encore",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "galbrena": {
        "kit_name": "Galbrena",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "hiyuki": {
        "kit_name": "Hiyuki",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "iuno": {
        "kit_name": "Iuno",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "jianxin": {
        "kit_name": "Jianxin",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "jinhsi": {
        "kit_name": "Jinhsi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "jiyan": {
        "kit_name": "Jiyan",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lingyang": {
        "kit_name": "Lingyang",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lucilla": {
        "kit_name": "Lucilla",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lucy": {
        "kit_name": "Lucy",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lumi": {
        "kit_name": "Lumi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lupa": {
        "kit_name": "Lupa",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "luuk herssen": {
        "kit_name": "Luuk Herssen",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "lynae": {
        "kit_name": "Lynae",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "mornye": {
        "kit_name": "Mornye",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "mortefi": {
        "kit_name": "Mortefi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "phrolova": {
        "kit_name": "Phrolova",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "phoebe": {
        "kit_name": "Phoebe",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "qiuyuan": {
        "kit_name": "Qiuyuan",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "qingxiao": {
        "kit_name": "Qingxiao",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rebecca": {
        "kit_name": "Rebecca",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "roccia": {
        "kit_name": "Roccia",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover aero": {
        "kit_name": "Rover Aero",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover spectro": {
        "kit_name": "Rover Spectro",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover glacio": {
        "kit_name": "Rover Glacio",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover electro": {
        "kit_name": "Rover Electro",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover fusion": {
        "kit_name": "Rover Fusion",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover havoc": {
        "kit_name": "Rover Havoc",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "rover": {
        "kit_name": "Rover",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "sanhua": {
        "kit_name": "Sanhua",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "shorekeeper": {
        "kit_name": "Shorekeeper",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "sigrika": {
        "kit_name": "Sigrika",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "suisui": {
        "kit_name": "SuiSui",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "taoqi": {
        "kit_name": "Taoqi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "verina": {
        "kit_name": "Verina",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "xiangli yao": {
        "kit_name": "Xiangli Yao",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "yangyang": {
        "kit_name": "Yangyang",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição da Yangyang..."},
            {"name": "Habilidade de Ressonância", "description": "..."},
            {"name": "Circuito Forte", "description": "..."},
            {"name": "Liberação de Ressonância", "description": "..."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "xuanling": {
        "kit_name": "Xuanling",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição da Xuanling..."},
            {"name": "Habilidade de Ressonância", "description": "..."},
            {"name": "Circuito Forte", "description": "..."},
            {"name": "Liberação de Ressonância", "description": "..."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "yinlin": {
        "kit_name": "Yinlin",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "youhu": {
        "kit_name": "Youhu",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "yuanwu": {
        "kit_name": "Yuanwu",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "zani": {
        "kit_name": "Zani",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
    "zhezhi": {
        "kit_name": "Zhezhi",
        "skills": [
            {"name": "Ataque Básico", "description": "Descrição detalhada do ataque básico."},
            {"name": "Habilidade de Ressonância", "description": "Descrição da habilidade de ressonância."},
            {"name": "Circuito Forte", "description": "Descrição do circuito forte."},
            {"name": "Liberação de Ressonância", "description": "Descrição da liberação de ressonância."},
        ],
        "team_buffs": [("Bônus de Equipe", 0.0)],
        "personal_buffs": [("Bônus Pessoal", 0.0)],
        "markers": [("Marcador", 0.0)],
    },
}

MANUAL_CHARACTER_KITS["augusta"]["skills"] = [
    {
        "name": "Ataque Básico - Caminho da Caçadora",
        "description": (
            "• Combo Básico: Até 4 golpes consecutivos de Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
            "• ATQ Pesado - Choque de Aço: Consome <font color='#eab308'><b>Vigor</b></font> e causa Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
            "• ATQ Aéreo e Contra-ataque de Esquiva: Ataques de mergulho e Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
            "• <font color='#a855f7'><b>Proeza Cheia</b></font>: Desbloqueia Trovão Rugidor: Recuo, Corte Giratório e Uppercut."
        ),
    },
    {
        "name": "Habilidade de Ressonância: Lâmina da Guerreira",
        "description": (
            "• Lâmina da Guerreira: Augusta salta e golpeia o chão, causando Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
            "• Contra-ATQ Evasivo: Luz Solar Eterna - Golpe causa Dano de Habilidade de Ressonância.<br>"
            "• Com Ascendência cheia, ataques no chão e no ar podem encadear no Luz Solar Imortal - Salto."
        ),
    },
    {
        "name": "Circuito Forte - Invoca-me pelo Sol",
        "description": (
            "• Luz Solar Imortal - Golpe substitui a Lâmina da Guerreira com Ascendência cheia.<br>"
            "• Luz Solar Imortal - Salto causa Dano <font color='#a855f7'><b>Voltaico</b></font> e pode ser realizada no ar.<br>"
            "• Luz Solar Imortal - Mergulho consome Ascendência e causa Dano de ATQ Pesado.<br>"
            "• Cada Mergulho concede 1 acúmulo de <font color='#a855f7'><b>Majestade</b></font>.<br>"
            "• <font color='#a855f7'><b>Ascendência</b></font>: acumula até 100 pontos com ataques e habilidades."
        ),
    },
    {
        "name": "Liberação de Ressonância - Conquista em Direção ao Sol",
        "description": (
            "• Espada do Juramento Eterno: Varre o Espadão e causa Dano <font color='#a855f7'><b>Voltaico</b></font> de ATQ Pesado.<br>"
            "• Sublime é o Sol: Com 2 acúmulos de Majestade, entra em Lealdade Jurada por 7s.<br>"
            "• Solisnato e Protetor Semprebrilho causam Dano de ATQ Pesado e encerram o estado.<br>"
            "• Reino da Governante: Dura 30s e concede escudo aos Ressonantes da equipe."
        ),
    },
    {
        "name": "Habilidade Intro - Passo da Chama Dourada",
        "description": (
            "• Passo da Chama Dourada causa Dano <font color='#a855f7'><b>Voltaico</b></font>.<br>"
            "• Concede 20% de <font color='#a855f7'><b>Ascendência</b></font>."
        ),
    },
    {
        "name": "Habilidade Outro - Canção de Batalha dos Inflexíveis",
        "description": (
            "• O próximo Ressonante recebe 15% de amplificação de Dano por 14s.<br>"
            "• Augusta ganha 1 acúmulo de <font color='#a855f7'><b>Majestade</b></font> e 1 de Coroa de Vontades.<br>"
            "• Coroa de Vontades aumenta o Dano <font color='#a855f7'><b>Voltaico</b></font>."
        ),
    },
    {
        "name": "Habilidade Inata 1 - Favor da Glória",
        "description": (
            "• Ao causar dano, Augusta ganha um escudo por 5s.<br>"
            "• O efeito pode ser ativado uma vez a cada 0.5s e não é acumulável."
        ),
    },
    {
        "name": "Habilidade Inata 2 - Bravura Calcinante",
        "description": (
            "• Após 4s fora de combate, restaura <font color='#a855f7'><b>Majestade</b></font> se estiver abaixo de 1 acúmulo.<br>"
            "• Restaura completamente a Coroa de Vontades."
        ),
    },
]
