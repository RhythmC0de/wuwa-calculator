"""Character image URLs database."""

# * EDITAVEL: adicione "id": {"char": URL, "weapon": URL} para novas imagens.
# ! Use somente URLs HTTPS permitidas pela politica em app/security_policy.py.

# Diagnóstico: linhas 120-125 (rover:*), usam o mesmo URL Wikia e podem falhar
# por certificado TLS expirado; as URLs foram preservadas intencionalmente.

CHARACTER_IMAGE_FALLBACKS = {
    "suisui": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/suisui-sprite-s"
            "m.webp"
        ),
        "weapon": "https://i.imgur.com/r7ChV8Y.png",
    },
    "lucilla": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lucilla-sprite-"
            "sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/freezeframe.webp",
    },
    "xuanling": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/yangyang-xuanli"
            "ng-sprite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/azureoath.webp",
    },
    "lucy": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lucy-sprite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/spectraltrigger.webp",
    },
    "rebecca": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/rebecca-sprite-"
            "sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/skullthrasher.webp",
    },
    "denia": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/denia-sprite-sm"
            ".webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/forgeddwarfstar.webp",
    },
    "hiyuki": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/hiyuki-sprite-s"
            "m.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/frostburn.webp",
    },
    "sigrika": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/sigrika-sprite-"
            "sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/solswornciphers.webp",
    },
    "luuk herssen": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/luuk-herssen-sp"
            "rite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/daybreakersspine.webp",
    },
    "aemeath": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/aemeath-sprite-"
            "sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/everbrightpolestar.webp",
    },
    "mornye": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/mornye-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://wuwalab.com/images/weapons/starfieldcalibrator.webp"
        ),
    },
    "lynae": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lynae-sprite-sm"
            ".webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/spectrumblaster.webp",
    },
    "chisa": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/chisa-sprite-sm"
            ".webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/kumokiri.webp",
    },
    "galbrena": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/galbrena-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/lux-umbra.webp"
        ),
    },
    "iuno": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/iuno-sprite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/moongazerssigil.webp",
    },
    "augusta": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/augusta-sprite-"
            "sm.webp"
        ),
        "weapon": (
            "https://wuwalab.com/images/weapons/thunderflaredominion.webp"
        ),
    },
    "phrolova": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/phrolova-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/lethean-eleg"
            "y.webp"
        ),
    },
    "zani": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/zani-sprite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/blazingjustice.webp",
    },
    "ciaccona": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/ciaccona-sprite"
            "-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/woodlandaria.webp",
    },
    "cartethyia": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/cartethyia-spri"
            "te-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/defiersthorn.webp",
    },
    "lupa": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lupa-sprite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/wildfiremark.webp",
    },
    "cantarella": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/cantarella-spri"
            "te-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/whispers-of-"
            "sirens.webp"
        ),
    },
    "brant": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/brant-sprite-sm"
            ".webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/unflickering"
            "-valor.webp"
        ),
    },
    "qingxiao": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/qingxiao-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/glint-of-clo"
            "uds.webp"
        ),
    },
    "phoebe": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/phoebe-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/luminous-hym"
            "n.webp"
        ),
    },
    "shorekeeper": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/shorekeeper-spr"
            "ite-sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/stellarsymphony.webp",
    },
    "xiangli yao": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/xiangli-yao-spr"
            "ite-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/verity-s-han"
            "dle.webp"
        ),
    },
    "jingran": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/jingran-sprite-"
            "sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/thousandfold"
            "-deliverance.webp"
        ),
    },
    "zhezhi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/zhezhi-sprite-s"
            "m.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/rimedrapedsprouts.webp",
    },
    "changli": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/changli-sprite-"
            "sm.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/blazingbrilliance.webp",
    },
    "jiyan": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/jiyan-sprite-sm"
            ".webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/verdant-summ"
            "it.webp"
        ),
    },
    "jinhsi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/jinhsi-sprite-s"
            "m.webp"
        ),
        "weapon": "https://wuwalab.com/images/weapons/agesofharvest.webp",
    },
    "yinlin": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/yinlin-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/stringmaster"
            ".webp"
        ),
    },
    "aalto": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/aalto-sprite-sm"
            ".webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/the-last-dan"
            "ce.webp"
        ),
    },
    "baizhi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/baizhi-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/stellar-symp"
            "hony.webp"
        ),
    },
    "buling": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/buling-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/stellar-symp"
            "hony.webp"
        ),
    },
    "calcharo": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/calcharo-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/lustrous-raz"
            "or.webp"
        ),
    },
    "camellya": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/camellya-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/red-spring.webp"
        ),
    },
    "carlotta": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/carlotta-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/the-last-dan"
            "ce.webp"
        ),
    },
    "chixia": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/chixia-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/the-last-dan"
            "ce.webp"
        ),
    },
    "danjin": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/danjin-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/blazing-bril"
            "liance.webp"
        ),
    },
    "encore": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/encore-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/stringmaster"
            ".webp"
        ),
    },
    "jianxin": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/jianxin-sprite-"
            "sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/verity-s-han"
            "dle.webp"
        ),
    },
    "lingyang": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lingyang-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/abyss-surges"
            ".webp"
        ),
    },
    "lumi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/lumi-sprite-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/lustrous-raz"
            "or.webp"
        ),
    },
    "mortefi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/mortefi-sprite-"
            "sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/static-mist.webp"
        ),
    },
    "roccia": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/roccia-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/tragicomedy.webp"
        ),
    },
    "rover spectro": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "rover havoc": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "rover aero": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "rover glacio": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "rover fusion": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "rover electro": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/blazing-bril"
            "liance.webp"
        ),
    },
    "rover": {
        "char": "https://i.imgur.com/X5jSM7S.png",
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "sanhua": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/sanhua-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "taoqi": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/taoqi-sprite-sm"
            ".webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/dauntless-ev"
            "ernight.webp"
        ),
    },
    "verina": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/verina-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/stellar-symp"
            "hony.webp"
        ),
    },
    "youhu": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/youhu-sprite-sm"
            ".webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/abyss-surges"
            ".webp"
        ),
    },
    "yangyang": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/yangyang-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-of-g"
            "enesis.webp"
        ),
    },
    "yangyang xuanling": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/yangyang-sprite"
            "-sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/azure-oath.webp"
        ),
    },
    "yuanwu": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/yuanwu-sprite-s"
            "m.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/ages-of-harv"
            "est.webp"
        ),
    },
    "qiuyuan": {
        "char": (
            "https://rackoon.com.br/images/wuwa/resonators/qiuyuan-sprite-"
            "sm.webp"
        ),
        "weapon": (
            "https://rackoon.com.br/images/wuwa/weapons-items/emerald-sent"
            "ence.webp"
        ),
    },
}
