#!/usr/bin/env python3
"""
批量导入 Obsidian 文章到 articles.json
自动按文件名匹配，不手动拼路径，避免引号问题
"""

import json, os, re
from datetime import datetime
from pathlib import Path

VAULT = Path("/Users/luoclaw/Library/Mobile Documents/iCloud~md~obsidian/Documents/andy's obsidian")
WEBSITE_DIR = "/Users/luoclaw/WorkBuddy/成果库/骆驼商业本质"
OUT = os.path.join(WEBSITE_DIR, "articles.json")

# ── 文章清单：用 (id, pillar, category, subcategory, filename_glob, tags, importance)
# filename_glob 只需能唯一匹配文件名片段即可
ARTICLES_SPEC = [
    # 🌌 世界观
    ("world-essence-full",      "worldview", "世界观",   "世界的真相", "2-世界的本质-完整版",
     ["世界本质","真相","哲学"], 5),
    ("world-fake",              "worldview", "世界观",   "世界的真相", "5-理解",
     ["世界是假的","认知"], 4),
    ("break-all-forms",          "worldview", "世界观",   "世界的真相", "6-破一切相",
     ["破相","哲学"], 4),
    ("ding-jing-kong",          "worldview", "世界观",   "世界的真相", "7-分别",
     ["定","净","空","哲学"], 3),
    ("mind-appears-form",        "worldview", "世界观",   "世界的真相", "8-起心显相",
     ["一念花开","心相一体"], 4),
    ("nature-reality",           "worldview", "世界观",   "世界的真相", "9-世界是虚妄的本质",
     ["性相不二","虚妄","世界观"], 4),
    ("karma-nature",            "worldview", "世界观",   "世界的真相", "10-性相+业力构成世界",
     ["业力","性相","世界原理"], 4),

    # 🏛️ 社会逻辑 — Obsidian 02-经济研究/

    # ── 经济总纲
    ("moc-9042",                    "social",    "社会逻辑", "经济总纲",    "MOC-经济研究总纲",
     ["经济总纲","经济研究","总纲"], 2),

    # ── 一、经济史研究
    ("moc-45a6",                    "social",    "社会逻辑", "经济史研究",   "MOC-经济史",
     ["经济史研究","经济史"], 2),
    # · 世界历史
    ("2026-8299",                   "social",    "社会逻辑", "世界历史",    "全球经济民主国家政党制度对比",
     ["世界历史","民主国家","全球经济","政党制度","对比"], 3),
    ("eco-4f35",                    "social",    "社会逻辑", "世界历史",    "欧洲简史",
     ["世界历史","欧洲简史"], 3),
    ("eco-8067",                    "social",    "社会逻辑", "世界历史",    "美国打压遏制日本发展的历史",
     ["世界历史","美国","日本","发展"], 3),
    # · 中国历史
    ("300-ee33",                    "social",    "社会逻辑", "中国历史",    "中国 300 年一次的朝代更替的原因",
     ["中国历史","朝代更替","周期"], 3),
    ("eco-f3ff",                    "social",    "社会逻辑", "中国历史",    "中国历代开国皇帝",
     ["中国历史","开国皇帝"], 3),
    ("eco-24f9",                    "social",    "社会逻辑", "中国历史",    "中国的未来发展周期",
     ["中国历史","未来","发展周期"], 3),
    ("eco-90e5",                    "social",    "社会逻辑", "中国历史",    "从几次亚洲金融危机，看经济发展的规律",
     ["中国历史","亚洲金融危机","经济规律"], 4),
    ("eco-b11c",                    "social",    "社会逻辑", "中国历史",    "唐史传承线：从李唐开国到唐玄宗",
     ["中国历史","唐朝","李唐"], 3),
    ("eco-a945",                    "social",    "社会逻辑", "中国历史",    "武则天登顶核心博弈逻辑",
     ["中国历史","武则天","博弈"], 4),

    # ── 二、宏观经济与周期研究
    # · 宏观经济
    ("wealth-delusion",             "social",    "社会逻辑", "宏观经济",    "01-财富的谬论",
     ["财富","谬论","经济"], 5),
    ("wealth-delusion-summary",     "social",    "社会逻辑", "宏观经济",    "02-财富的谬论",
     ["财富","总结"], 4),
    ("moc-d2cd",                    "social",    "社会逻辑", "宏观经济",    "MOC-宏观经济",
     ["宏观经济"], 2),
    ("eco-f428",                    "social",    "社会逻辑", "宏观经济",    "中国经济周期研究",
     ["宏观经济","经济周期"], 3),
    ("eco-42bf",                    "social",    "社会逻辑", "宏观经济",    "从人的五十岁到达顶峰看经济周期规律",
     ["宏观经济","经济周期","规律"], 3),
    ("eco-779f",                    "social",    "社会逻辑", "宏观经济",    "卢麒元对社会的五种分类",
     ["宏观经济","社会分类","卢麒元"], 3),
    ("eco-764d",                    "social",    "社会逻辑", "宏观经济",    "家庭或个人",
     ["宏观经济","财富","归零"], 3),
    ("eco-800d",                    "social",    "社会逻辑", "宏观经济",    "经济危机",
     ["宏观经济","经济学","经济危机"], 4),
    ("eco-3667",                    "social",    "社会逻辑", "宏观经济",    "第三次世界大危机",
     ["宏观经济","世界大战","危机"], 3),
    # · 500年大周期
    ("500-overview",                "social",    "社会逻辑", "500年大周期", "一、世界500年大周期概述",
     ["500年","大周期","概述"], 5),
    ("500-mode-iteration",          "social",    "社会逻辑", "500年大周期", "二、世界500年霸权",
     ["霸权","模式更迭"], 5),
    ("500-iteration-essence",       "social",    "社会逻辑", "500年大周期", "三、世界500年大周期",
     ["迭代","周期本质"], 4),
    ("500-cycle-logic",             "social",    "社会逻辑", "500年大周期", "四、世界统治霸权",
     ["周期循环","霸权逻辑"], 4),
    ("500-management",              "social",    "社会逻辑", "500年大周期", "从管理维度",
     ["管理维度","大国周期"], 4),
    ("500-industry",                "social",    "社会逻辑", "500年大周期", "产业维度",
     ["产业维度","预测"], 4),
    ("500-core-hegemony",           "social",    "社会逻辑", "500年大周期", "七、核心霸权周期",
     ["核心霸权","预测"], 5),
    ("500-germany",                 "social",    "社会逻辑", "500年大周期", "八、德国没有崛起的原因",
     ["德国","崛起","霸权"], 3),
    ("500-france1",                 "social",    "社会逻辑", "500年大周期", "九、法国为什么没有崛起",
     ["法国","霸权"], 3),
    ("500-france2",                 "social",    "社会逻辑", "500年大周期", "十、法国没有成为霸主",
     ["法国","霸主"], 3),
    ("500-china-us",                "social",    "社会逻辑", "500年大周期", "十一、中美未来争霸",
     ["中美","争霸","未来"], 5),
    ("500-key-nodes",               "social",    "社会逻辑", "500年大周期", "十二、500年霸权周期重要节点",
     ["重要节点","霸权周期"], 4),
    ("500-five-dimensions",         "social",    "社会逻辑", "500年大周期", "十三、总结世界大周围",
     ["五维霸权","总结"], 5),
    ("500-control-system",          "social",    "社会逻辑", "500年大周期", "十四、全球霸权控制体系",
     ["霸权控制","全球体系"], 4),
    ("500-three-layer",             "social",    "社会逻辑", "500年大周期", "十五、三层霸权模型图解",
     ["三层模型","霸权图解"], 4),
    ("500-moc",                     "social",    "社会逻辑", "500年大周期", "MOC-500年全球大周期全景图",
     ["MOC","全景图"], 3),

    # ── 三、国际金融与政策研究
    # · 国际金融
    ("moc-2e0a",                    "social",    "社会逻辑", "国际金融",    "MOC-国际金融",
     ["国际金融"], 2),
    ("eco-46ba",                    "social",    "社会逻辑", "国际金融",    "特朗普上台",
     ["国际金融","美国战略","特朗普"], 3),
    ("eco-86c0",                    "social",    "社会逻辑", "国际金融",    "美元重构",
     ["国际金融","美元","重构"], 3),
    ("eco-4540",                    "social",    "社会逻辑", "国际金融",    "世界三大财团",
     ["国际金融","财团"], 3),
    ("2026-befb",                   "social",    "社会逻辑", "国际金融",    "民主国家",
     ["国际金融","民主国家","制度对比"], 3),
    ("eco-f1af",                    "social",    "社会逻辑", "国际金融",    "华盛顿共识",
     ["国际金融","华盛顿共识"], 3),
    ("eco-1e42",                    "social",    "社会逻辑", "国际金融",    "数字货币单词",
     ["国际金融","数字货币"], 3),
    ("eco-9367",                    "social",    "社会逻辑", "国际金融",    "泰国，柬埔寨",
     ["国际金融","泰国","柬埔寨","冲突"], 3),
    ("201-664a",                    "social",    "社会逻辑", "国际金融",    "石油霸权2.0 1",
     ["国际金融","石油霸权"], 3),
    ("20-5755",                     "social",    "社会逻辑", "国际金融",    "石油霸权2.0",
     ["国际金融","石油霸权"], 3),
    ("eco-9b3d",                    "social",    "社会逻辑", "国际金融",    "美元加息",
     ["国际金融","美元加息"], 3),
    ("2026-d178",                   "social",    "社会逻辑", "国际金融",    "马斯克对未来预期2026年",
     ["国际金融","马斯克","预期"], 3),
    # · 美国战略
    ("us-strategy-dollar",          "social",    "社会逻辑", "美国战略",    "美国搅动全球局势的战略与美元周期",
     ["美国","美元","地缘"], 5),
    ("us-global-looting",           "social",    "社会逻辑", "美国战略",    "美国全球掠夺",
     ["美国","掠夺","全球"], 4),
    ("us-2026-policy",              "social",    "社会逻辑", "美国战略",    "2026美国对外政策",
     ["美国","2026","对外政策"], 4),
    ("us-2017-2026-sanctions",      "social",    "社会逻辑", "美国战略",    "20017-2026美国对外制裁",
     ["美国","制裁","2017-2026"], 3),

    # ── 四、中国经济观察
    ("moc-ac66",                    "social",    "社会逻辑", "中国经济",    "MOC-中国经济",
     ["中国经济"], 2),
    ("2025-7107",                   "social",    "社会逻辑", "中国经济",    "2025中央民营企业工作会议",
     ["中国经济","民营企业","中央"], 3),
    ("eco-0483",                    "social",    "社会逻辑", "中国经济",    "中国六大芯片企业",
     ["中国经济","芯片"], 3),
    ("eco-745d",                    "social",    "社会逻辑", "中国经济",    "农村改革～中央一号文件",
     ["中国经济","农村改革"], 3),
    ("eco-e7dd",                    "social",    "社会逻辑", "中国经济",    "商业模式",
     ["中国经济","商业模式"], 3),
    ("eco-8511",                    "social",    "社会逻辑", "中国经济",    "李嘉诚",
     ["中国经济","李嘉诚"], 3),
    ("eco-0338",                    "social",    "社会逻辑", "中国经济",    "民营企业中央会议名单",
     ["中国经济","民营企业","名单"], 3),
    ("eco-4180",                    "social",    "社会逻辑", "中国经济",    "海南封关的战略意义",
     ["中国经济","海南","封关"], 3),


    # 🧘 思想与修行
    ("human-essence",           "worldview",  "世界观",   "世界的真相", "1-人的本质",
     ["人的本质","人性","修身"], 5),
    ("one-thought-flower",       "worldview",  "世界观",   "世界的真相", "14-一念花开",
     ["一念花开","心性","修行"], 4),
    ("inner-sage-outer-king",   "worldview",  "世界观",   "内圣外王", "01-内圣外王的核心思想",
     ["内圣外王","儒家","修身"], 5),
    ("inner-sage-dao",          "worldview",  "世界观",   "内圣外王", "02-内圣外王儒道区别",
     ["儒道","内圣外王","区别"], 4),
    ("inner-sage-laozi",        "worldview",  "世界观",   "内圣外王", "03-从",
     ["老子","内圣外王","道家"], 4),
    ("inner-sage-mind-form",     "worldview",  "世界观",   "内圣外王", "04-从",
     ["心相一体","内圣外王"], 4),
    ("dou-dou-core",            "worldview",  "世界观",   "豆豆三部曲", "解读豆豆三部曲核心思想",
     ["豆豆三部曲","文化","修行"], 3),
    ("dou-dou-meaning",         "worldview",  "世界观",   "豆豆三部曲", "豆豆三部曲想表达什么",
     ["豆豆三部曲","文化"], 3),

    # 🆕 传统哲学 — 新增（Obsidian 排版后入库）
    ("taiji-tushuo",            "worldview", "世界观",   "传统哲学",   "《太极图说》",
     ["太极","宋明理学","周敦颐","哲学","世界观"], 5),
    ("daodejing-vs-fo",         "worldview", "世界观",   "传统哲学",   '道德经',
     ["道德经","佛","区别","哲学"], 4),
    ("zhouyi-books-intro",      "worldview", "世界观",   "传统哲学",   "周易相关书籍介绍",
     ["周易","易经","书籍","经典"], 3),
    ("computer-ai-future",      "worldview", "世界观",   "意识哲学",   '计算机',
     ["计算机","AI","未来","哲学"], 3),
    ("world-bottom-logic",      "worldview", "世界观",   "世界的真相", "3-世界的底层逻辑",
     ["底层逻辑","世界","真相"], 4),
    ("consciousness-slice-world","worldview","世界观",   "世界的真相", "4-意识切片世界观",
     ["意识","切片","世界观","哲学"], 5),
    ("human-needs-theory",      "worldview", "世界观",   "世界的真相", "11-人的需求论",
     ["需求论","人性","哲学"], 3),
    ("world-four-dimensions",   "worldview", "世界观",   "世界的真相", "世界真相：四个维度",
     ["四个维度","真相","世界观"], 4),
    ("tiandao-didao-rendao",    "worldview", "世界观",   "世界的真相", "天道，地道，人道",
     ["天道","地道","人道","三才"], 4),
    ("consciousness-ai-truth",  "worldview", "世界观",   "世界的真相", "意识的真相：从AI现象到底层逻辑",
     ["意识","AI","底层逻辑","真相"], 5),
    ("consciousness-moltbook",  "worldview", "世界观",   "世界的真相", "从Moltbook数字宗教",
     ["Moltbook","数字宗教","意识","自主本质"], 4),
    ("truth-is-defined",        "worldview", "世界观",   "世界的真相", "17-真相",
     ["真相","定义","认知","哲学"], 4),
    ("journey-west-philosophy", "worldview", "世界观",   "西游记", "西游记01-三阶段",
     ["西游记","哲学思想","文化"], 3),
    ("journey-west-daoist",     "worldview", "世界观",   "西游记", "西游记-02-五行山",
     ["西游记","道家","哲学"], 3),
    ("journey-west-buddhist",   "worldview", "世界观",   "西游记", "孙悟空五行山明心见性",
     ["西游记","佛家","哲学"], 3),
    ("journey-west-moc",        "worldview", "世界观",   "西游记", "MOC-西游哲学",
     ["西游记","MOC","哲学"], 2),

    # 📖 儒家思想研究（5篇）
    ("confucianism-moc",        "worldview", "世界观",   "儒家思想研究", "MOC-儒家思想",
     ["儒家","MOC"], 3),
    ("confucianism-heritage",   "worldview", "世界观",   "儒家思想研究", "儒家思想传承",
     ["儒家","传承","孔子","理学"], 4),
    ("confucianism-dynasties",  "worldview", "世界观",   "儒家思想研究", "儒释道三家与朝代更迭关系",
     ["儒家","释道","朝代","历史","哲学"], 4),
    ("zeng-guofan-mistakes",    "worldview", "世界观",   "儒家思想研究", "曾国藩：人生三大错误",
     ["曾国藩","人生","错误"], 3),
    ("wang-yangming-xinxue",    "worldview", "世界观",   "儒家思想研究", "王阳明心学核心思想",
     ["王阳明","心学","儒家","哲学"], 5),

    # 🔬 科学哲学研究（3篇）
    ("taiji-wave-particle",     "worldview", "世界观",   "科学哲学研究", "太极与波粒二象性",
     ["太极","波粒二象性","科学","哲学"], 5),
    ("unified-field-theory",    "worldview", "世界观",   "科学哲学研究", "统一场论",
     ["统一场论","宇宙","力学","物理学","理论"], 5),
    ("science-philosophy-moc",  "worldview", "世界观",   "科学哲学研究", "MOC-科学哲学",
     ["科学哲学","MOC"], 3),

# 佛学思想研究（自动生成，共 69 篇）
    ("buddha", "worldview", "佛学思想研究", "佛陀的核心思想", "01-释迦牟尼佛法思想总纲", ["佛陀的核心思想"], 3),
    ("buddha1", "worldview", "佛学思想研究", "佛陀的核心思想", "02-四圣谛", ["佛陀的核心思想"], 3),
    ("buddha2", "worldview", "佛学思想研究", "佛陀的核心思想", "03-八正道", ["佛陀的核心思想"], 3),
    ("buddha3", "worldview", "佛学思想研究", "佛陀的核心思想", "04-十二因缘：三世两重因果梳理", ["佛陀的核心思想"], 3),
    ("buddha4", "worldview", "佛学思想研究", "佛陀的核心思想", "05-三法印", ["佛陀的核心思想"], 3),
    ("buddha5", "worldview", "佛学思想研究", "佛陀的核心思想", "06-四念处：深度止观四念处的解析", ["佛陀的核心思想"], 3),
    ("buddha6", "worldview", "佛学思想研究", "佛陀的核心思想", "07-佛陀思想完整逻辑闭环解析", ["佛陀的核心思想"], 3),
    ("buddha7", "worldview", "佛学思想研究", "佛陀的核心思想", "MOC-佛陀核心思想", ["佛陀的核心思想"], 3),
    ("buddha8", "worldview", "佛学思想研究", "心与识", "01-觉～空～慈悲心", ["心与识"], 3),
    ("buddha9", "worldview", "佛学思想研究", "心与识", "02-破分别心：直击“比较”分别心的核心", ["心与识"], 3),
    ("buddha10", "worldview", "佛学思想研究", "心与识", "03-心识-打分机制与修行破局", ["心与识"], 3),
    ("buddha11", "worldview", "佛学思想研究", "心与识", "04-分别心的底层逻辑：从凡夫境界到佛法修证", ["心与识"], 3),
    ("buddha12", "worldview", "佛学思想研究", "心与识", "05-人心与 AI 的终极对照与修行破法", ["心与识"], 3),
    ("buddha13", "worldview", "佛学思想研究", "心与识", "06-三界唯心", ["心与识"], 3),
    ("buddha14", "worldview", "佛学思想研究", "心与识", "07-修行的功夫：静心与明理", ["心与识"], 3),
    ("buddha15", "worldview", "佛学思想研究", "心与识", "08-观心的原理-破心之道", ["心与识"], 3),
    ("buddha16", "worldview", "佛学思想研究", "心与识", "09-心如工画师", ["心与识"], 3),
    ("buddha17", "worldview", "佛学思想研究", "心与识", "10-心识运作原理与照见", ["心与识"], 3),
    ("buddha18", "worldview", "佛学思想研究", "心与识", "MOC-心与识", ["心与识"], 3),
    ("buddha19", "worldview", "佛学思想研究", "金刚经", "00 · 金刚经原文及白话对照版", ["金刚经"], 3),
    ("buddha20", "worldview", "佛学思想研究", "金刚经", "01-《金刚经》核心要义·三段式完整框架", ["金刚经"], 3),
    ("buddha21", "worldview", "佛学思想研究", "金刚经", "02-《金刚经》终极三段式逻辑解析", ["金刚经"], 3),
    ("buddha22", "worldview", "佛学思想研究", "金刚经", "03-金刚经核心要义总结", ["金刚经"], 3),
    ("buddha23", "worldview", "佛学思想研究", "金刚经", "04-《金刚经》“五眼”解释及观修口诀", ["金刚经"], 3),
    ("buddha24", "worldview", "佛学思想研究", "金刚经", "05-所谓…，即非…，是名…", ["金刚经"], 3),
    ("buddha25", "worldview", "佛学思想研究", "金刚经", "06-五蕴的详细解释与核心要点", ["金刚经"], 3),
    ("buddha26", "worldview", "佛学思想研究", "金刚经", "07-金刚经第十八品解析", ["金刚经"], 3),
    ("buddha27", "worldview", "佛学思想研究", "金刚经", "08-金刚经「如来悉知悉见」段落", ["金刚经"], 3),
    ("buddha28", "worldview", "佛学思想研究", "金刚经", "MOC-金刚经", ["金刚经"], 3),
    ("buddha29", "worldview", "佛学思想研究", "金刚经", "《金刚经》核心思想总纲", ["金刚经"], 3),
    ("buddha30", "worldview", "佛学思想研究", "佛教思想", "MOC-佛教思想", ["佛教思想"], 3),
    ("buddha31", "worldview", "佛学思想研究", "佛教思想", "何为净土", ["佛教思想"], 3),
    ("buddha32", "worldview", "佛学思想研究", "佛教思想", "佛教“五见”", ["佛教思想"], 3),
    ("buddha33", "worldview", "佛学思想研究", "佛教思想", "佛教“见”分类", ["佛教思想"], 3),
    ("buddha34", "worldview", "佛学思想研究", "佛教思想", "大成佛教与小成佛教的区别", ["佛教思想"], 3),
    ("buddha35", "worldview", "佛学思想研究", "佛教思想", "如何解释寺庙与拜佛“性相”不二的道理", ["佛教思想"], 3),
    ("buddha36", "worldview", "佛学思想研究", "止观禅定", "01-禅定境界", ["止观禅定"], 3),
    ("buddha37", "worldview", "佛学思想研究", "止观禅定", "02-四禅八定", ["止观禅定"], 3),
    ("buddha38", "worldview", "佛学思想研究", "止观禅定", "03-四禅八定→灭尽定→涅槃", ["止观禅定"], 3),
    ("buddha39", "worldview", "佛学思想研究", "止观禅定", "04-浅释四禅八定：禅定修行的四层清净与四重心空", ["止观禅定"], 3),
    ("buddha40", "worldview", "佛学思想研究", "止观禅定", "05-观止修行总纲", ["止观禅定"], 3),
    ("buddha41", "worldview", "佛学思想研究", "止观禅定", "06-止观：奢摩他与毗婆舍那修行路径", ["止观禅定"], 3),
    ("buddha42", "worldview", "佛学思想研究", "止观禅定", "07-深度止观训练：止-从粗住到无色界定", ["止观禅定"], 3),
    ("buddha43", "worldview", "佛学思想研究", "止观禅定", "08-深度止观训练：观（毗婆舍那）的系统解析", ["止观禅定"], 3),
    ("buddha44", "worldview", "佛学思想研究", "止观禅定", "09-观呼吸：体会“放”与“盯”，看见真实的观", ["止观禅定"], 3),
    ("buddha45", "worldview", "佛学思想研究", "止观禅定", "MOC-止观禅定", ["止观禅定"], 3),
    ("buddha46", "worldview", "佛学思想研究", "修行方法", "01-《因果.轮回》核心逻辑体系", ["修行方法"], 3),
    ("buddha47", "worldview", "佛学思想研究", "修行方法", "02-《因果·轮回》破相修行工具", ["修行方法"], 3),
    ("buddha48", "worldview", "佛学思想研究", "修行方法", "03-“内观”—七种观", ["修行方法"], 3),
    ("buddha49", "worldview", "佛学思想研究", "修行方法", "04-“我执”与“心动”的三要素循环机理", ["修行方法"], 3),
    ("buddha50", "worldview", "佛学思想研究", "修行方法", "05-破“取相”停止心动的修行机制", ["修行方法"], 3),
    ("buddha51", "worldview", "佛学思想研究", "修行方法", "06-破心执", ["修行方法"], 3),
    ("buddha52", "worldview", "佛学思想研究", "修行方法", "07-从三破法到漏尽通的终极圆满之路", ["修行方法"], 3),
    ("buddha53", "worldview", "佛学思想研究", "修行方法", "08-修炼的过程", ["修行方法"], 3),
    ("buddha54", "worldview", "佛学思想研究", "修行方法", "09-修心能得到什么", ["修行方法"], 3),
    ("buddha55", "worldview", "佛学思想研究", "修行方法", "10-圣多纳释放法（Sedona Method）", ["修行方法"], 3),
    ("buddha56", "worldview", "佛学思想研究", "修行方法", "MOC-修行方法", ["修行方法"], 3),
    ("buddha57", "worldview", "佛学思想研究", "禅宗六祖", "MOC-禅宗六祖", ["禅宗六祖"], 3),
    ("buddha58", "worldview", "佛学思想研究", "禅宗六祖", "六祖证悟", ["禅宗六祖"], 3),
    ("buddha59", "worldview", "佛学思想研究", "禅宗六祖", "猜话头，观念头的本质", ["禅宗六祖"], 3),
    ("buddha60", "worldview", "佛学思想研究", "中观唯识", "01-龙树菩萨：中观逻辑", ["中观唯识"], 3),
    ("buddha61", "worldview", "佛学思想研究", "中观唯识", "02-龙树菩萨的修行三句密语", ["中观唯识"], 3),
    ("buddha62", "worldview", "佛学思想研究", "中观唯识", "03-世俗谛与胜义谛区别", ["中观唯识"], 3),
    ("buddha63", "worldview", "佛学思想研究", "中观唯识", "04-中观：八不偈", ["中观唯识"], 3),
    ("buddha64", "worldview", "佛学思想研究", "中观唯识", "05-中观_世俗谛_空性", ["中观唯识"], 3),
    ("buddha65", "worldview", "佛学思想研究", "中观唯识", "06-《唯识》", ["中观唯识"], 3),
    ("buddha66", "worldview", "佛学思想研究", "中观唯识", "07-中观与唯识～1", ["中观唯识"], 3),
    ("buddha67", "worldview", "佛学思想研究", "中观唯识", "08-中观与唯识 ～2", ["中观唯识"], 3),
    ("buddha68", "worldview", "佛学思想研究", "中观唯识", "MOC-中观唯识", ["中观唯识"], 3),
]


def find_file(glob_fragment, vault_root):
    """在 vault 中递归搜索包含 glob_fragment 的 .md 文件，返回第一个匹配"""
    candidates = []
    for p in vault_root.rglob("*.md"):
        if glob_fragment in p.name:
            candidates.append(p)
    if candidates:
        # 优先返回最短路径匹配（最精确）
        candidates.sort(key=lambda p: len(p.name))
        return str(candidates[0].relative_to(vault_root))
    return None


def read_file(rel_path):
    try:
        with open(vault / rel_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"  ⚠️  读取失败: {rel_path} -> {e}")
        return ""


def clean_md(text):
    text = re.sub(r'^---\n.*?\n---', '', text, flags=re.DOTALL)
    text = re.sub(r'!\[$$.*?$$\]\(.*?\)', '', text)
    text = re.sub(r'#\d+ ', '# ', text)
    # 清理 Obsidian 特有的 HTML font/color 标签，保留内容
    text = re.sub(r'<font[^>]*>', '', text)
    text = re.sub(r'</font>', '', text)
    text = re.sub(r'<br\s*/?>', '\n', text)
    # 清理其他 HTML 标签但保留内容
    text = re.sub(r'</?span[^>]*>', '', text)
    text = re.sub(r'</?div[^>]*>', '', text)
    return text.strip()


def extract_title(content, filename):
    """
    提取文章标题。
    Obsidian 中文件名就是文章标题，优先用文件名。
    文件名不可用时才 fallback 到 H1。
    """
    name = filename.replace('.md', '').strip()

    # 文件名非空就直接用（Obsidian 文件名即标题）
    if name:
        return name

    # fallback：从 H1 提取
    m = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return name


def file_mtime(rel_path):
    try:
        ts = os.path.getmtime(vault / rel_path)
        return datetime.fromtimestamp(ts).strftime('%Y-%m')
    except:
        return '2026-06'


# ── 主流程 ─────────────────────────────────────────
vault = VAULT
print(f"🔍 Vault: {VAULT}")

articles = []
not_found = []

for (aid, pillar, category, subcategory, glob_frag, tags, importance) in ARTICLES_SPEC:
    rel = find_file(glob_frag, vault)
    if not rel:
        not_found.append((aid, glob_frag))
        print(f"  ❌ 未找到: [{aid}] {glob_frag}")
        continue

    content = read_file(rel)
    if not content:
        print(f"  ⚠️  空内容: {rel}")
        continue

    # 先清理再提取标题（避免HTML标签干扰）
    cleaned = clean_md(content)
    title    = extract_title(cleaned, os.path.basename(rel))
    date_str = file_mtime(rel)
    summary  = cleaned[:200].replace('\n', ' ').replace('#', '')[:120]

    articles.append({
        "id":           aid,
        "pillar":       pillar,
        "category":     category,
        "subcategory":  subcategory,
        "title":        title,
        "date":         date_str,
        "summary":      summary + ("..." if len(cleaned) > 120 else ""),
        "tags":         tags,
        "importance":   importance,
        "content":      cleaned,
        "wordCount":    len(cleaned),
        "sourcePath":   rel,
    })
    print(f"  ✅ {aid}: {title[:35]} ({len(content)}字)")

if not_found:
    print(f"\n⚠️  未匹配到 {len(not_found)} 篇：")
    for (aid, frag) in not_found:
        print(f"     {aid} <- {frag}")

out = {
    "meta": {
        "version":   "1.0",
        "generated": datetime.now().isoformat(),
        "count":     len(articles)
    },
    "articles": articles
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# Also generate articles.js for script-tag loading (compatible with file:// protocol)
js_data = json.dumps(out, ensure_ascii=False, indent=2)
WEBSITE_DIR = os.path.dirname(OUT)
with open(os.path.join(WEBSITE_DIR, "articles.js"), "w", encoding="utf-8") as f:
    f.write(f"window.__ARTICLES__ = {js_data};")

size_kb = os.path.getsize(OUT) // 1024
js_path = os.path.join(WEBSITE_DIR, "articles.js")
js_size_kb = os.path.getsize(js_path) // 1024
print(f"\n✅ 完成！共 {len(articles)} 篇文章 → {OUT}")
print(f"   articles.json: {size_kb} KB")
print(f"   articles.js: {js_size_kb} KB")
