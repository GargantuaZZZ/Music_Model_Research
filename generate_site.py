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
        "papers": papers,
    }
    REPORT_PATH.write_text("const REPORT_DATA = " + json.dumps(report, ensure_ascii=False, indent=2) + ";\n")
    print(f"Wrote {REPORT_PATH.name} with {len(papers)} papers")


if __name__ == "__main__":
    main()
