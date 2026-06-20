import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "ismir2025_papers_raw.json"
REPORT_PATH = ROOT / "report_data.js"


CATEGORY_RULES = [
    {
        "id": "understanding",
        "name": "音乐信号理解与识别",
        "short": "理解 / 识别",
        "color": "#2563eb",
        "description": "从音频、乐谱或多模态音乐数据中识别结构、内容、语义和演奏属性。",
        "keywords": [
            "classification", "recognition", "detection", "estimation", "transcription",
            "retrieval", "recommendation", "tagging", "emotion", "mood", "genre",
            "instrument", "pitch", "beat", "downbeat", "tempo", "chord", "harmony",
            "tonality", "alignment", "synchronization", "score following", "structure",
            "segmentation", "lyrics", "singing", "vocal", "voice", "omr", "optical music",
            "performance", "expression", "timbre", "features", "query", "search",
            "music signal processing", "symbolic music processing", "mir tasks",
        ],
    },
    {
        "id": "separation",
        "name": "音乐分离、分轨与源建模",
        "short": "分离 / 分轨",
        "color": "#dc2626",
        "description": "把混合音乐拆成声部、乐器、人声、鼓组或其它可编辑音轨，也包括伴奏/人声消除和声源定位。",
        "keywords": [
            "separation", "source separation", "demixing", "stem", "stems", "track separation",
            "multi-track", "multitrack", "vocal separation", "singing voice separation",
            "accompaniment", "drum", "bass", "instrument separation",
            "bleeding", "remix", "music demixing",
        ],
    },
    {
        "id": "generation",
        "name": "音乐生成、编辑与创作工具",
        "short": "生成 / 编辑",
        "color": "#16a34a",
        "description": "生成音频、符号音乐、伴奏、歌词或可控编辑音乐内容，关注创作交互和评估。",
        "keywords": [
            "generation", "generative", "generate", "synthesis", "composition",
            "composer", "editing", "edit", "style transfer", "arrangement", "accompaniment generation",
            "diffusion", "latent diffusion", "language model", "llm", "large language model", "transformer",
            "musiclm", "text-to-music", "text to music", "prompt", "controllable",
            "controlnet", "creative", "co-creative", "improvisation", "automatic music", "symbolic generation",
        ],
    },
    {
        "id": "datasets_eval",
        "name": "数据集、评测与可复现性",
        "short": "数据 / 评测",
        "color": "#9333ea",
        "description": "提出数据集、基准、评估方法、开放工具或复现实验流程，是 MIR 近年非常重要的基础设施层。",
        "keywords": [
            "dataset", "datasets", "corpus", "benchmark", "evaluation",
            "reproducibility", "open source", "annotation", "annotations", "label",
            "labels", "ground truth", "mirex", "challenge", "leaderboard",
            "novel datasets and use cases",
        ],
    },
    {
        "id": "human_culture",
        "name": "人、文化、产业与音乐学",
        "short": "人文 / 应用",
        "color": "#ea580c",
        "description": "围绕听众、音乐家、文化语境、版权伦理、教育和产业应用展开，常与计算方法结合。",
        "keywords": [
            "user", "listener", "human", "culture", "cultural", "musicology",
            "musicological", "education", "therapy", "copyright", "ethics", "bias",
            "fairness", "industry", "recommendation", "playlist", "social", "behavior",
            "dance", "performance practice", "expressive", "emotion", "aesthetics",
        ],
    },
    {
        "id": "methods",
        "name": "方法论、表示学习与模型分析",
        "short": "方法 / 表征",
        "color": "#0891b2",
        "description": "研究训练目标、表征学习、弱监督、鲁棒性、可解释性和 MIR 通用方法。",
        "keywords": [
            "representation", "embedding", "self-supervised", "supervised", "weakly",
            "contrastive", "pretraining", "pre-trained", "foundation", "model",
            "learning", "neural", "transformer", "diffusion", "interpretability",
            "explainability", "robustness", "domain adaptation", "transfer",
            "loss", "optimization", "dynamic time warping", "methodology",
            "inversion", "flow matching", "equivariant", "synthesizer",
            "machine learning/artificial intelligence for music", "mir fundamentals",
        ],
    },
]


TREND_RULES = [
    ("foundation", "基础模型 / 大模型进入 MIR", ["foundation", "large language model", "llm", "pretrained", "pre-trained", "self-supervised", "transformer", "prompt", "language model"]),
    ("data", "数据集与评测仍是硬通货", ["dataset", "corpus", "benchmark", "evaluation", "metric", "annotation", "reproducibility", "mirex"]),
    ("symbolic_audio", "音频与符号表示正在合流", ["symbolic", "musicxml", "midi", "score", "omr", "audio", "alignment", "synchronization"]),
    ("generation_control", "生成研究转向可控、可评估、可编辑", ["generation", "generative", "editing", "controllable", "prompt", "diffusion", "synthesis", "composition"]),
    ("human_context", "MIR 越来越关心真实使用场景", ["user", "listener", "education", "culture", "musicology", "industry", "recommendation", "copyright", "ethics"]),
]


STOPWORDS = {
    "music", "musical", "mir", "using", "based", "learning", "model", "models", "analysis",
    "towards", "system", "systems", "data", "audio", "paper", "approach", "method",
    "methods", "new", "study", "task", "tasks", "through", "from", "with", "for",
    "and", "the", "of", "in", "to", "on", "a", "an", "is", "are", "by",
}

READING_LEVELS = {
    "deep_dive": {"name": "深挖/复现", "short": "深挖", "rank": 3},
    "close_read": {"name": "精读", "short": "精读", "rank": 2},
    "broad_read": {"name": "泛读", "short": "泛读", "rank": 1},
    "scan": {"name": "标题摘要扫读", "short": "扫读", "rank": 0},
}

READING_TARGETS = {
    "deep_dive": {
        "understanding": 2,
        "methods": 1,
        "generation": 2,
        "datasets_eval": 1,
        "separation": 2,
        "human_culture": 0,
    },
    "close_read": {
        "understanding": 7,
        "methods": 5,
        "generation": 4,
        "datasets_eval": 3,
        "separation": 2,
        "human_culture": 1,
    },
    "broad_read": {
        "understanding": 14,
        "methods": 7,
        "generation": 4,
        "datasets_eval": 6,
        "separation": 1,
        "human_culture": 5,
    },
}

MODALITY_RULES = [
    ("audio", "音频", ["audio", "recording", "sound", "waveform", "spectrogram", "vocal", "singing", "source", "binaural"]),
    ("symbolic", "符号/乐谱", ["symbolic", "midi", "score", "musicxml", "tablature", "chord", "harmony", "omr", "sheet"]),
    ("multimodal", "多模态", ["multimodal", "video", "image", "lyrics", "text", "album cover", "vision"]),
    ("user", "用户/行为", ["user", "listener", "playlist", "recommendation", "learning", "diary", "cross-cultural"]),
]

MODEL_RULES = [
    ("foundation", "基础模型/预训练", ["foundation", "pretrained", "pre-trained", "self-supervised", "contrastive", "embedding"]),
    ("llm", "LLM/语言条件", ["llm", "large language model", "language model", "prompt", "instruction", "natural language"]),
    ("diffusion", "扩散/生成模型", ["diffusion", "flow matching", "controlnet", "generative"]),
    ("transformer", "Transformer/序列模型", ["transformer", "bert", "attention"]),
    ("classical", "规则/统计/传统方法", ["dynamic time warping", "shortest path", "histogram", "rule", "statistical"]),
]

TASK_RULES = [
    ("transcription", "转录/标注", ["transcription", "annotation", "notes", "pitch", "tablature"]),
    ("segmentation", "结构/分段", ["segmentation", "structure", "form"]),
    ("retrieval", "检索/推荐", ["retrieval", "recommendation", "fingerprinting", "playlist"]),
    ("generation", "生成/编辑", ["generation", "editing", "synthesis", "composition", "text-to-music"]),
    ("separation", "分离/分轨", ["separation", "demixing", "source separation", "stem"]),
    ("omr", "OMR/乐谱理解", ["omr", "optical music", "sheet music", "score"]),
    ("evaluation", "评测/数据", ["evaluation", "dataset", "benchmark", "metric", "corpus"]),
]


def normalize(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def score_text(text, keywords):
    text = text.lower()
    total = 0
    for kw in keywords:
        pattern = r"(?<![a-z0-9])" + re.escape(kw.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            total += 1
    return total


def classify(paper):
    title = paper["title"].lower()
    abstract = " ".join([paper["abstract"], paper["tldr"]]).lower()
    keywords = " ".join(paper["keywords"]).lower()
    scores = {}
    for rule in CATEGORY_RULES:
        value = 3 * score_text(title, rule["keywords"])
        value += 1.4 * score_text(abstract, rule["keywords"])
        value += 0.7 * score_text(keywords, rule["keywords"])
        scores[rule["id"]] = value
    # Conference taxonomy keywords can make infrastructure papers look broader than they are.
    # Keep data/evaluation as a primary label only when the title or abstract carries that signal.
    hard_data_hits = score_text(title, ["dataset", "corpus", "benchmark", "evaluation", "annotation", "reproducibility", "mirex"])
    soft_data_hits = score_text(abstract, ["dataset", "corpus", "benchmark", "evaluation", "annotation", "reproducibility", "mirex"])
    if hard_data_hits == 0 and soft_data_hits < 2:
        scores["datasets_eval"] *= 0.45
    max_score = max(scores.values()) if scores else 0
    primary = "understanding"
    if max_score > 0:
        primary = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    secondary = [cid for cid, value in sorted(scores.items(), key=lambda kv: -kv[1]) if value > 0 and cid != primary][:3]
    confidence = min(0.95, 0.35 + 0.15 * max_score)
    return primary, secondary, scores, confidence


def words(text):
    return re.findall(r"[a-z][a-z0-9-]{2,}", text.lower())


def first_match(text, rules, fallback):
    text = text.lower()
    for _, label, keywords in rules:
        if score_text(text, keywords):
            return label
    return fallback


def infer_matrix_fields(paper):
    blob = " ".join([paper["title"], paper["abstract"], " ".join(paper["keywords"])])
    task = first_match(blob, TASK_RULES, "综合 MIR 任务")
    modality = first_match(blob, MODALITY_RULES, "待从正文确认")
    model_family = first_match(blob, MODEL_RULES, "待从正文确认")
    eval_focus = first_match(blob, [
        ("metric", "指标/benchmark 对比", ["metric", "benchmark", "evaluation", "score", "accuracy", "f-measure", "sdr"]),
        ("dataset", "数据集/标注质量", ["dataset", "corpus", "annotation", "ground truth"]),
        ("human", "用户研究/感知评价", ["user", "listener", "perceptual", "human", "diary"]),
        ("repro", "复现/开放资源", ["open source", "reproducibility", "code", "release"]),
    ], "待从正文确认")
    notes = "先核对问题定义、数据来源、baseline、指标是否支撑摘要结论。"
    return {
        "task": task,
        "modality": modality,
        "modelFamily": model_family,
        "evaluationFocus": eval_focus,
        "matrixNote": notes,
    }


def priority_score(paper, trend_hits):
    blob = " ".join([paper["title"], paper["abstract"], " ".join(paper["keywords"])]).lower()
    score = 0
    score += 6 if "awards nominee" in blob else 0
    score += 4 if paper.get("pdf") else 0
    score += int(paper["confidence"] * 6)
    score += len(paper["secondary"])
    score += sum(1 for ids in trend_hits.values() if paper["id"] in ids)
    score += 3 if score_text(blob, ["foundation", "llm", "diffusion", "source separation", "benchmark", "dataset", "evaluation"]) else 0
    score += 2 if paper["primary"] in {"generation", "separation", "methods"} else 0
    return score


def assign_reading_levels(papers, trend_hits):
    for p in papers:
        p["priorityScore"] = priority_score(p, trend_hits)
        p["readingLevel"] = "scan"
    remaining = {p["id"]: p for p in papers}

    for level in ["deep_dive", "close_read", "broad_read"]:
        for cid, target in READING_TARGETS[level].items():
            candidates = [p for p in remaining.values() if p["primary"] == cid]
            candidates.sort(key=lambda p: (-p["priorityScore"], p["title"]))
            for paper in candidates[:target]:
                paper["readingLevel"] = level
                remaining.pop(paper["id"], None)


def build_research_plan(papers):
    level_counts = Counter(p["readingLevel"] for p in papers)
    category_level_counts = defaultdict(Counter)
    for p in papers:
        category_level_counts[p["primary"]][p["readingLevel"]] += 1

    return {
        "summary": [
            "采用三级阅读：标题摘要扫读 111 篇，泛读 60-70 篇，精读 24-30 篇，深挖/复现 6-8 篇。",
            "目标是建立 MIR 领域认知地图：任务谱系、数据模态、模型范式、评测方式、产业落点和未来机会。",
            "默认周期为 4 周；如果要写综述或做复现实验，可扩展到 6 周。"
        ],
        "readingLevels": READING_LEVELS,
        "levelCounts": dict(level_counts),
        "quotaByCategory": {
            cid: {
                "category": CATEGORY_RULES[[r["id"] for r in CATEGORY_RULES].index(cid)]["short"],
                "deep": category_level_counts[cid]["deep_dive"],
                "close": category_level_counts[cid]["close_read"],
                "broad": category_level_counts[cid]["broad_read"],
                "scan": category_level_counts[cid]["scan"],
                "total": sum(category_level_counts[cid].values()),
            }
            for cid in [rule["id"] for rule in CATEGORY_RULES]
        },
        "phases": [
            {"name": "第 1 阶段：领域地图", "duration": "2-3 天", "goal": "扫读全部标题、摘要、关键词，建立六类 taxonomy。"},
            {"name": "第 2 阶段：泛读", "duration": "7-10 天", "goal": "泛读 60-70 篇，记录任务、输入输出、数据、模型、指标、结论和局限。"},
            {"name": "第 3 阶段：精读", "duration": "10-14 天", "goal": "精读 24-30 篇，每篇写 1 页笔记，重点核对实验设计与 baseline。"},
            {"name": "第 4 阶段：深挖/复现", "duration": "7-10 天", "goal": "选择 6-8 篇做代码、数据、实验级深挖，优先看生成编辑、分离、foundation model 和评测协议。"},
            {"name": "第 5 阶段：综合输出", "duration": "2-3 天", "goal": "形成趋势报告、论文矩阵、方向建议和可做 demo 列表。"},
        ],
        "understandingGoals": [
            "区分 MIR 的三层问题：音乐信号层、音乐结构/语义层、音乐创作与交互层。",
            "判断哪些任务已经成熟，哪些任务仍卡在数据、评测或产品定义上。",
            "识别一篇论文到底贡献任务、数据、模型、评测、工具，还是音乐学/用户洞察。",
            "理解大模型适合做表征、检索、标注辅助、生成控制和交互，但不能替代音乐结构、音频质量和评测协议。",
            "最终能回答：大家在做什么，哪些方向正在汇合，我们值得切入哪里。",
        ],
        "deliverables": [
            "论文阅读矩阵：111 篇条目，包含分类、阅读等级、任务、模态、模型、数据/指标和备注。",
            "精读笔记集：24-30 篇，每篇 500-1000 字。",
            "趋势报告：5-7 个趋势，每个趋势至少 3 篇证据论文。",
            "方向建议：推荐 3 个可继续做的方向，如可解释音乐理解、可控音乐编辑、分离与生成式混音、MIR 评测工具。",
        ],
        "qualityChecks": [
            "每个趋势结论至少对应 3 篇论文证据。",
            "每个精读结论必须回到 PDF 的实验、图表或指标。",
            "LLM 只用于初筛、归纳、对比和生成问题清单；引用、实验结果、数据规模必须人工核对。",
            "报告需让不了解 MIR 的读者 20 分钟内理解领域结构，让研究者 5 分钟内看到潜在切入点。",
        ],
        "directions": [
            {"title": "可解释音乐理解", "text": "连接转录、结构、和声、表演分析和弱监督训练，适合做可视化诊断工具。"},
            {"title": "可控音乐编辑", "text": "聚焦 instruction editing、text-to-music、codec/diffusion 与客观评测，最接近可演示产品。"},
            {"title": "分离与生成式混音", "text": "把 source separation、spatial audio、用户引导分离和生成式编辑合在一起，适合做创作工作流。"},
            {"title": "MIR 评测工具", "text": "围绕数据去重、benchmark、主观/客观指标一致性，建立比单模型更稳定的研究资产。"},
        ],
    }


def main():
    raw = json.loads(RAW_PATH.read_text())
    papers = []
    for item in raw:
        content = item.get("content", {})
        title = normalize(content.get("title"))
        abstract = normalize(content.get("abstract") or content.get("TLDR"))
        tldr = normalize(content.get("TLDR") or abstract)
        keywords = [normalize(k) for k in content.get("keywords", []) if normalize(k)]
        paper = {
            "id": str(item.get("id", "")),
            "title": title,
            "abstract": abstract,
            "tldr": tldr,
            "authors": content.get("authors", []),
            "keywords": keywords,
            "session": str(item.get("session") or (content.get("session") or [""])[0]),
            "day": str(content.get("day", "")),
            "presentation": content.get("paper_presentation", ""),
            "pdf": content.get("pdf_path", ""),
            "poster": content.get("poster_pdf", ""),
            "video": content.get("video", ""),
            "sourceUrl": f"https://ismir2025program.ismir.net/poster_{item.get('id')}.html",
        }
        primary, secondary, scores, confidence = classify(paper)
        paper.update({
            "primary": primary,
            "secondary": secondary,
            "scores": scores,
            "confidence": round(confidence, 2),
        })
        papers.append(paper)

    category_meta = {rule["id"]: {k: rule[k] for k in ("name", "short", "color", "description")} for rule in CATEGORY_RULES}
    category_counts = Counter(p["primary"] for p in papers)
    secondary_counts = Counter(cid for p in papers for cid in p["secondary"])
    session_counts = defaultdict(Counter)
    for p in papers:
        session_counts[p["session"]][p["primary"]] += 1

    keyword_counts = Counter()
    method_counts = Counter()
    trend_hits = {tid: [] for tid, _, _ in TREND_RULES}
    for p in papers:
        blob = " ".join([p["title"], p["abstract"], " ".join(p["keywords"])]).lower()
        for kw in p["keywords"]:
            if kw.lower() not in {"open review", "mir tasks", "applications"}:
                keyword_counts[kw] += 1
        for w in words(blob):
            if w not in STOPWORDS and len(w) > 3:
                method_counts[w] += 1
        for tid, _, kws in TREND_RULES:
            if any(kw in blob for kw in kws):
                trend_hits[tid].append(p["id"])

    trends = []
    for tid, title, _ in TREND_RULES:
        ids = trend_hits[tid]
        sample = [p for p in papers if p["id"] in set(ids)][:5]
        trends.append({
            "id": tid,
            "title": title,
            "count": len(ids),
            "paperIds": ids,
            "examples": [{"id": p["id"], "title": p["title"], "primary": p["primary"]} for p in sample],
        })

    assign_reading_levels(papers, trend_hits)
    for paper in papers:
        paper.update(infer_matrix_fields(paper))

    category_insights = {
        "understanding": "最大板块仍是理解与识别：多音高、和弦、节拍、结构、歌词、OMR、表演分析等传统 MIR 任务继续活跃，但越来越多地引入弱监督、预训练和跨模态表征。",
        "separation": "分离/分轨在 ISMIR 2025 不是数量最大的明面主题，但它与生成式编辑、混音、数据集和评测紧密相连；适合继续追踪 MUSDB、MDX/MVSEP、音频 foundation model 与可控编辑交叉处。",
        "generation": "生成方向的关键词从“能生成”转向“可控、可编辑、可评估”：文本/语义条件、符号-音频桥接、创作交互和客观评测是更值得深挖的入口。",
        "datasets_eval": "数据集、标注、评测与复现占比很高，说明 MIR 研究仍强依赖可检验的任务定义。对新方向来说，好的数据协议往往比单一模型更能形成影响力。",
        "human_culture": "人文与应用类研究把 MIR 拉回真实音乐生态：听众、演奏者、教育、文化差异、推荐和版权伦理会影响模型目标本身。",
        "methods": "方法论论文强调如何训练、解释和泛化 MIR 模型。大模型能提供强表征，但领域知识、对齐、标注噪声和评测仍决定结果是否可信。",
    }

    routes = [
        {
            "title": "路线 A：先做领域地图",
            "text": "用 ISMIR 标题、摘要、关键词建立 taxonomy：任务层、数据模态层、模型层、评测层。先看数量和交叉，再挑论文精读。",
        },
        {
            "title": "路线 B：围绕三大产品能力",
            "text": "把论文映射到理解/识别、分离/分轨、生成/编辑三类用户能力，分别追问输入输出、数据依赖、评价指标和可落地难点。",
        },
        {
            "title": "路线 C：让大模型辅助，但保留证据链",
            "text": "LLM 适合做初筛、归纳和改写；每个结论都回链到标题、摘要、关键词和论文 PDF，尤其不要直接相信模型生成的引用与实验结论。",
        },
        {
            "title": "路线 D：找自己想做的切口",
            "text": "我会优先关注“可解释的音乐理解 + 可控编辑”：它连接信号理解、分离和生成，也最容易形成可演示的网站或工具。",
        },
    ]

    report = {
        "source": {
            "name": "ISMIR 2025 Papers",
            "url": "https://ismir2025program.ismir.net/papers.html",
            "capturedAt": "2026-06-20",
            "paperCount": len(papers),
            "note": "分类由本地脚本基于题目、摘要、关键词启发式生成，适合作为调研入口，不替代论文精读。",
        },
        "categories": category_meta,
        "categoryCounts": dict(category_counts),
        "secondaryCounts": dict(secondary_counts),
        "sessionCounts": {s: dict(c) for s, c in sorted(session_counts.items())},
        "topKeywords": keyword_counts.most_common(24),
        "topTerms": method_counts.most_common(36),
        "trends": trends,
        "categoryInsights": category_insights,
        "routes": routes,
        "researchPlan": build_research_plan(papers),
        "papers": papers,
    }
    REPORT_PATH.write_text("const REPORT_DATA = " + json.dumps(report, ensure_ascii=False, indent=2) + ";\n")
    print(f"Wrote {REPORT_PATH.name} with {len(papers)} papers")


if __name__ == "__main__":
    main()
