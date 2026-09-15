[33mcommit 4dc61879e863077baed24c392932b195d3dc038f[m[33m ([m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: Matheus <promttest18@gmail.com>
Date:   Tue Sep 15 00:29:31 2026 -0300

    reorganização do codigo
    
    ainda falta coisa

M	main.py
R100	app/__init__.py	src/wuwa_calculator/app/__init__.py
R092	app/backend_adapter.py	src/wuwa_calculator/app/backend_adapter.py
R100	app/banner_service.py	src/wuwa_calculator/app/banner_service.py
R099	app/components.py	src/wuwa_calculator/app/components.py
R099	app/dps_simulation_panel.py	src/wuwa_calculator/app/dps_simulation_panel.py
R098	app/history_tab.py	src/wuwa_calculator/app/history_tab.py
R099	app/history_video_player.py	src/wuwa_calculator/app/history_video_player.py
R098	app/home_tab.py	src/wuwa_calculator/app/home_tab.py
R098	app/main.py	src/wuwa_calculator/app/main.py
R098	app/multimedia_tab.py	src/wuwa_calculator/app/multimedia_tab.py
R098	app/resonator_tab.py	src/wuwa_calculator/app/resonator_tab.py
R100	app/security_policy.py	src/wuwa_calculator/app/security_policy.py
R100	app/styles.py	src/wuwa_calculator/app/styles.py
R098	app/teams_tab.py	src/wuwa_calculator/app/teams_tab.py
R100	app/wuwa_processing.py	src/wuwa_calculator/app/wuwa_processing.py
R099	app/wuwa_tracker_adapter.py	src/wuwa_calculator/app/wuwa_tracker_adapter.py
R100	data/__init__.py	src/wuwa_calculator/data/__init__.py
R100	data/catalog_overrides.json	src/wuwa_calculator/data/catalog_overrides.json
A	src/wuwa_calculator/data/characters/data/aalto/aalto.json
A	src/wuwa_calculator/data/characters/data/aemeath/aemeath.json
A	src/wuwa_calculator/data/characters/data/augusta/augusta.json
A	src/wuwa_calculator/data/characters/data/baizhi/baizhi.json
A	src/wuwa_calculator/data/characters/data/brant/brant.json
A	src/wuwa_calculator/data/characters/data/buling/buling.json
A	src/wuwa_calculator/data/characters/data/calcharo/calcharo.json
A	src/wuwa_calculator/data/characters/data/camellya/camellya.json
A	src/wuwa_calculator/data/characters/data/cantarella/cantarella.json
A	src/wuwa_calculator/data/characters/data/carlotta/carlotta.json
A	src/wuwa_calculator/data/characters/data/cartethyia/cartethyia.json
A	src/wuwa_calculator/data/characters/data/changli/changli.json
A	src/wuwa_calculator/data/characters/data/chisa/chisa.json
A	src/wuwa_calculator/data/characters/data/chixia/chixia.json
A	src/wuwa_calculator/data/characters/data/ciaccona/ciaccona.json
A	src/wuwa_calculator/data/characters/data/danji/danji.json
A	src/wuwa_calculator/data/characters/data/denia/denia.json
A	src/wuwa_calculator/data/characters/data/encore/encore.json
A	src/wuwa_calculator/data/characters/data/galbrena/galbrena.json
A	src/wuwa_calculator/data/characters/data/hiyuki/hiyuki.json
A	src/wuwa_calculator/data/characters/data/hsin/hsin.json
A	src/wuwa_calculator/data/characters/data/iuno/iuno.json
A	src/wuwa_calculator/data/characters/data/jianxin/jianxin.json
A	src/wuwa_calculator/data/characters/data/jingran/jingran.json
A	src/wuwa_calculator/data/characters/data/jinhsi/jinhsi.json
A	src/wuwa_calculator/data/characters/data/jinshi/jinshi.json
A	src/wuwa_calculator/data/characters/data/jiyan/jiyan.json
A	src/wuwa_calculator/data/characters/data/lingyang/lingyang.json
A	src/wuwa_calculator/data/characters/data/lucilla/lucilla.json
A	src/wuwa_calculator/data/characters/data/lucy/lucy.json
A	src/wuwa_calculator/data/characters/data/lumi/lumi.json
A	src/wuwa_calculator/data/characters/data/lupa/lupa.json
A	src/wuwa_calculator/data/characters/data/luuk_herssen/luuk_herssen.json
A	src/wuwa_calculator/data/characters/data/lynae/lynae.json
A	src/wuwa_calculator/data/characters/data/mornye/mornye.json
A	src/wuwa_calculator/data/characters/data/mortefi/mortefi.json
A	src/wuwa_calculator/data/characters/data/phoebe/phoebe.json
A	src/wuwa_calculator/data/characters/data/phrolova/phrolova.json
A	src/wuwa_calculator/data/characters/data/qingxiao/qingxiao.json
A	src/wuwa_calculator/data/characters/data/qiuyuan/qiuyuan.json
A	src/wuwa_calculator/data/characters/data/rebecca/rebecca.json
A	src/wuwa_calculator/data/characters/data/roccia/roccia.json
A	src/wuwa_calculator/data/characters/data/rover/rover.json
A	src/wuwa_calculator/data/characters/data/sanhua/sanhua.json
A	src/wuwa_calculator/data/characters/data/shorekeeper/shorekeeper.json
A	src/wuwa_calculator/data/characters/data/sigrika/sigrika.json
A	src/wuwa_calculator/data/characters/data/suisui/suisui.json
A	src/wuwa_calculator/data/characters/data/suoming/suoming.json
A	src/wuwa_calculator/data/characters/data/taoqi/taoqi.json
A	src/wuwa_calculator/data/characters/data/verina/verina.json
A	src/wuwa_calculator/data/characters/data/xiangli_yao/xiangli_yao.json
A	src/wuwa_calculator/data/characters/data/yangyang/yangyang.json
A	src/wuwa_calculator/data/characters/data/yangyang_xuanling/yangyang_xuanling.json
A	src/wuwa_calculator/data/characters/data/yinlin/yinlin.json
A	src/wuwa_calculator/data/characters/data/youhu/youhu.json
A	src/wuwa_calculator/data/characters/data/yuanwu/yuanwu.json
A	src/wuwa_calculator/data/characters/data/zani/zani.json
A	src/wuwa_calculator/data/characters/data/zezhi/zezhi.json
R100	utils/__init__.py	src/wuwa_calculator/data/characters/registry.json
A	src/wuwa_calculator/data/characters/skills/aalto/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/aalto/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/aalto/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/aalto/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/aalto/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/aalto/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/aemeath/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/aemeath/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/aemeath/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/aemeath/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/aemeath/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/aemeath/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/augusta/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/augusta/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/augusta/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/augusta/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/augusta/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/augusta/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/baizhi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/baizhi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/baizhi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/baizhi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/baizhi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/baizhi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/brant/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/brant/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/brant/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/brant/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/brant/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/brant/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/buling/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/buling/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/buling/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/buling/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/buling/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/buling/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/calcharo/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/calcharo/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/calcharo/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/calcharo/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/calcharo/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/calcharo/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/camellya/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/camellya/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/camellya/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/camellya/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/camellya/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/camellya/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/cantarella/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/cantarella/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/cantarella/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/cantarella/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/cantarella/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/cantarella/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/carlotta/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/carlotta/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/carlotta/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/carlotta/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/carlotta/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/carlotta/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/cartethyia/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/changli/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/changli/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/changli/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/changli/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/changli/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/changli/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/chisa/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/chisa/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/chisa/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/chisa/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/chisa/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/chisa/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/chixia/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/chixia/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/chixia/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/chixia/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/chixia/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/chixia/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/ciaccona/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/danji/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/danji/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/danji/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/danji/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/danji/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/danji/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/denia/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/denia/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/denia/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/denia/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/denia/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/denia/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/encore/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/encore/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/encore/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/encore/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/encore/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/encore/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/galbrena/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/galbrena/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/galbrena/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/galbrena/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/galbrena/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/galbrena/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/hiyuki/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/hsin/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/hsin/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/hsin/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/hsin/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/hsin/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/hsin/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/iuno/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/iuno/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/iuno/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/iuno/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/iuno/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/iuno/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/jianxin/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/jianxin/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/jianxin/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/jianxin/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/jianxin/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/jianxin/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/jingran/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/jingran/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/jingran/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/jingran/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/jingran/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/jingran/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/jinhsi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/jinshi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/jinshi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/jinshi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/jinshi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/jinshi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/jinshi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/jiyan/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/jiyan/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/jiyan/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/jiyan/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/jiyan/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/jiyan/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lingyang/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lingyang/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lingyang/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lingyang/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lingyang/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lingyang/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lucilla/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lucilla/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lucilla/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lucilla/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lucilla/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lucilla/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lucy/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lucy/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lucy/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lucy/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lucy/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lucy/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lumi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lumi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lumi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lumi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lumi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lumi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lupa/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lupa/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lupa/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lupa/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lupa/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lupa/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/luuk_herssen/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/lynae/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/lynae/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/lynae/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/lynae/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/lynae/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/lynae/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/mornye/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/mornye/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/mornye/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/mornye/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/mornye/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/mornye/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/mortefi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/mortefi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/mortefi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/mortefi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/mortefi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/mortefi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/phoebe/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/phoebe/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/phoebe/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/phoebe/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/phoebe/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/phoebe/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/phrolova/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/phrolova/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/phrolova/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/phrolova/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/phrolova/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/phrolova/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/qingxiao/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/qiuyuan/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rebecca/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rebecca/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rebecca/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rebecca/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rebecca/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rebecca/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/roccia/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/roccia/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/roccia/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/roccia/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/roccia/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/roccia/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/aero/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/eletro/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/fusion/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/glacio/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/havoc/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/rover/spectro/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/rover/variants.json
A	src/wuwa_calculator/data/characters/skills/sanhua/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/sanhua/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/sanhua/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/sanhua/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/sanhua/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/sanhua/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/shorekeeper/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/sigrika/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/sigrika/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/sigrika/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/sigrika/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/sigrika/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/sigrika/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/suisui/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/suisui/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/suisui/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/suisui/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/suisui/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/suisui/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/suoming/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/suoming/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/suoming/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/suoming/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/suoming/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/suoming/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/taoqi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/taoqi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/taoqi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/taoqi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/taoqi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/taoqi/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/verina/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/verina/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/verina/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/verina/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/verina/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/verina/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/xiangli_yao/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/yangyang/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/yangyang/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/yangyang/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/yangyang_xuanling/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/yinlin/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/yinlin/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/yinlin/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/yinlin/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/yinlin/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/yinlin/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/youhu/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/youhu/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/youhu/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/youhu/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/youhu/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/youhu/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/yuanwu/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/zani/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/zani/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/zani/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/zani/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/zani/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/zani/resonance_skill.json
A	src/wuwa_calculator/data/characters/skills/zezhi/basic_attack.json
A	src/wuwa_calculator/data/characters/skills/zezhi/forte_circuit.json
A	src/wuwa_calculator/data/characters/skills/zezhi/intro_skill.json
A	src/wuwa_calculator/data/characters/skills/zezhi/outro_skill.json
A	src/wuwa_calculator/data/characters/skills/zezhi/resonance_liberation.json
A	src/wuwa_calculator/data/characters/skills/zezhi/resonance_skill.json
R097	data/characters_elements.py	src/wuwa_calculator/data/characters_elements.py
R100	data/characters_ids.py	src/wuwa_calculator/data/characters_ids.py
R100	data/characters_kits.py	src/wuwa_calculator/data/characters_kits.py
R099	data/characters_quotes.py	src/wuwa_calculator/data/characters_quotes.py
R100	data/characters_stats.py	src/wuwa_calculator/data/characters_stats.py
R100	data/characters_urls.py	src/wuwa_calculator/data/characters_urls.py
R100	data/echoes.py	src/wuwa_calculator/data/echoes.py
A	src/wuwa_calculator/data/echoes/registry.json
R100	data/element_images.py	src/wuwa_calculator/data/element_images.py
R100	data/images.py	src/wuwa_calculator/data/images.py
R100	data/rotation_history.json	src/wuwa_calculator/data/rotation_history.json
A	src/wuwa_calculator/data/sonatas/registry.json
R100	data/team_saved_images.py	src/wuwa_calculator/data/team_saved_images.py
R100	data/teams.json	src/wuwa_calculator/data/teams.json
R100	data/weapons.py	src/wuwa_calculator/data/weapons.py
A	src/wuwa_calculator/data/weapons/registry.json
R100	storage/__init__.py	src/wuwa_calculator/storage/__init__.py
R100	storage/banner_cache.py	src/wuwa_calculator/storage/banner_cache.py
R100	storage/current_banner.json	src/wuwa_calculator/storage/current_banner.json
R100	storage/history_storage.py	src/wuwa_calculator/storage/history_storage.py
R100	storage/team_storage.py	src/wuwa_calculator/storage/team_storage.py
A	src/wuwa_calculator/storage/user_data/rotation_history.json
A	src/wuwa_calculator/storage/user_data/settings.json
A	src/wuwa_calculator/storage/user_data/teams.json
A	src/wuwa_calculator/ui/__init__.py
A	src/wuwa_calculator/ui/components/__init__.py
A	src/wuwa_calculator/ui/teams/__init__.py
R100	utils/Augusta.png	src/wuwa_calculator/utils/Augusta.png
A	src/wuwa_calculator/utils/__init__.py
R100	utils/augusta_preparada.png	src/wuwa_calculator/utils/augusta_preparada.png
R100	utils/image_processing.py	src/wuwa_calculator/utils/image_processing.py
R100	utils/localization.py	src/wuwa_calculator/utils/localization.py
R095	utils/ocr.py	src/wuwa_calculator/utils/ocr.py
R100	utils/process_icon.py	src/wuwa_calculator/utils/process_icon.py
A	tools/create_data.py
M	validate_data.py
