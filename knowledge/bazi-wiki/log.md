# Wiki 操作日志

> 所有 wiki 操作的时间记录。只追加。
> 操作类型：ingest, update, query, lint, create, archive, delete

## [2026-05-25] create | 八字命理知识库初始化
- 领域：中国传统八字命理学（子平法）
- 结构：SCHEMA.md, index.md, log.md + raw/, concepts/, entities/, methods/, queries/

## [2026-05-25] ingest | 渊海子平、神峰通考原典下载
- raw/classics/yuan-hai-zi-ping.md — 渊海子平原典（12章，来源：古文岛）
- raw/classics/shen-feng-tong-kao.md — 神峰通考原典（21章，来源：古文岛） 外部来源资料（4份原始文件）
- 移除：raw/tools/bazi-skill-wuxing-tables.md
- 移除：raw/tools/bazi-skill-shichen-table.md  
- 移除：raw/tools/bazi-skill-dayun-rules.md
- 移除：raw/tools/bazi-skill-classical-texts.md
- 所有引用页的 frontmatter sources 已清空

## [2026-05-25] create | 滴天髓阐微实战命例（8个案例）
### Cases 目录
- cases/index.md — 命例目录与分类索引
- cases/case-01-ren-tie-qiao.md — 任铁樵自评：从旺格
- cases/case-02-cai-ge-fu-gui.md — 正财格富贵：庚金财生杀
- cases/case-03-cai-ge-pin-jian.md — 偏财格破格贫贱：比劫夺财
- cases/case-04-sha-yin-xiang-sheng.md — 杀印相生武贵：丙火羊刃
- cases/case-05-shi-shen-zhi-sha.md — 食神制杀武贵：乙木得令
- cases/case-06-cong-ge.md — 从革格从旺：庚金旺极
- cases/case-07-guan-sha-hun-za.md — 官杀混杂动荡：己土伤官
- cases/case-08-tiao-hou.md — 调候命例冬金寒木：丙火解冻
- cases/case-09-shang-guan-pei-yin.md — 伤官佩印文贵：癸水伤官格
- cases/case-10-zheng-yin-ge.md — 正印格师儒之命：甲木得水
- cases/case-11-shang-guan-jian-guan.md — 伤官见官灾祸：癸水甲木克戊土
- cases/case-12-hua-qi-ge.md — 化气格甲己化土：全局土旺极
- cases/case-13-nu-ming-guan-xing.md — 女命官星透夫贵：己土甲木合
- cases/case-14-bi-jie-duo-cai.md — 比劫夺财破败：乙木比劫林立
- cases/case-15-cong-sha-ge.md — 从杀格弃命从杀：丁火从杀势
- cases/case-16-liang-qi-cheng-xiang.md — 两气成象金木相战：庚金子水通关
### Concepts — 古籍经典
- concepts/yuan-hai-zi-ping.md — 渊海子平：子平法奠基，十神体系、六亲、格局分类
- concepts/di-tian-sui.md — 滴天髓：旺衰气势论，天道/地道/人道三元体系
- concepts/zi-ping-zhen-quan.md — 子平真诠：格局论集大成，用神/相神/喜忌精准区分
- concepts/san-ming-tong-hui.md — 三命通会：命理百科全书，神煞大全
- concepts/qiong-tong-bao-jian.md — 穷通宝鉴：调候用神论，寒暖燥湿分析
- concepts/shen-feng-tong-kao.md — 神峰通考：病药说，批判神煞滥用
- concepts/qian-li-ming-gao.md — 千里命稿：实战断命技法，宫位论法
- concepts/xie-ji-bian-fang-shu.md — 协纪辨方书：神煞起例与择日
- concepts/guo-lao-xing-zong.md — 果老星宗：星命术（七政四余）与八字交叉

### Concepts (5)
- concepts/tian-gan-di-zhi.md — 天干地支（含藏干、冲合刑害）
- concepts/wu-xing.md — 五行（含生克、旺相休囚死）
- concepts/si-zhu.md — 四柱结构（含节气分界、五虎遁元）
- concepts/shi-shen.md — 十神（含详细解释和性格特征）
- concepts/da-yun-liu-nian.md — 大运与流年（含顺逆排法、起运计算）

### Entities (3)
- entities/shi-er-sheng-xiao.md — 十二生肖（含六合、三合、六冲）
- entities/shi-er-chang-sheng.md — 十二长生表（含用法说明）
- entities/ge-ju.md — 格局（含正格八格、变格体系）

### Methods (1)
- methods/pai-pan-bu-zhou.md — 排盘步骤（含完整流程和示例）
