"""Append short, clearly separated external summaries without rewriting RAG answers."""

from __future__ import annotations

import re
from collections.abc import Sequence

from integration.external_sources import ExternalSummary


MEASUREMENT_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(km|kilomet(?:er|re)s?|m|met(?:er|re)s?|mg\s*/\s*l|%|percent)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[^\W_]{3,}", re.UNICODE)

ADDITIONAL_INFORMATION_LABELS = {
    "en": "Additional information", "hi": "अतिरिक्त जानकारी", "kn": "ಹೆಚ್ಚುವರಿ ಮಾಹಿತಿ",
    "ta": "கூடுதல் தகவல்", "te": "అదనపు సమాచారం", "bn": "অতিরিক্ত তথ্য",
    "mr": "अतिरिक्त माहिती", "gu": "વધારાની માહિતી", "ml": "കൂടുതൽ വിവരങ്ങൾ",
    "pa": "ਵਾਧੂ ਜਾਣਕਾਰੀ", "ur": "اضافی معلومات", "or": "ଅତିରିକ୍ତ ସୂଚନା",
    "as": "অতিৰিক্ত তথ্য",
}
EXTERNAL_CONTEXT_LABELS = {
    "en": "External, community-edited context; not verified by the project knowledge base.",
    "hi": "बाहरी, समुदाय-संपादित संदर्भ; परियोजना के ज्ञान-आधार द्वारा सत्यापित नहीं।",
    "kn": "ಹೊರಗಿನ, ಸಮುದಾಯ-ಸಂಪಾದಿತ ಮಾಹಿತಿ; ಯೋಜನೆಯ ಜ್ಞಾನಭಂಡಾರದಿಂದ ಪರಿಶೀಲಿಸಲ್ಪಟ್ಟಿಲ್ಲ.",
    "ta": "வெளிப்புற, சமூகத்தால் திருத்தப்பட்ட தகவல்; திட்ட அறிவுத்தளத்தால் சரிபார்க்கப்படவில்லை.",
    "te": "బాహ్య, సమూహం సవరించిన సమాచారం; ప్రాజెక్ట్ నాలెడ్జ్ బేస్ ద్వారా ధృవీకరించబడలేదు.",
    "bn": "বাহ্যিক, সম্প্রদায়-সম্পাদিত তথ্য; প্রকল্পের জ্ঞানভান্ডার দ্বারা যাচাই করা হয়নি।",
    "mr": "बाह्य, समुदाय-संपादित संदर्भ; प्रकल्पाच्या ज्ञानसंग्रहाद्वारे पडताळलेला नाही.",
    "gu": "બાહ્ય, સમુદાય દ્વારા સંપાદિત સંદર્ભ; પ્રોજેક્ટના જ્ઞાન આધાર દ્વારા ચકાસાયેલ નથી.",
    "ml": "പുറത്തുനിന്നുള്ള, സമൂഹം തിരുത്തിയ വിവരം; പദ്ധതിയുടെ അറിവുശേഖരം പരിശോധിച്ചതല്ല.",
    "pa": "ਬਾਹਰੀ, ਭਾਈਚਾਰੇ ਵੱਲੋਂ ਸੰਪਾਦਿਤ ਜਾਣਕਾਰੀ; ਪ੍ਰੋਜੈਕਟ ਗਿਆਨ ਅਧਾਰ ਵੱਲੋਂ ਪ੍ਰਮਾਣਿਤ ਨਹੀਂ।",
    "ur": "بیرونی، کمیونٹی کی تدوین کردہ معلومات؛ منصوبے کے علمی ذخیرے سے تصدیق شدہ نہیں۔",
    "or": "ବାହ୍ୟ, ସମୁଦାୟ-ସମ୍ପାଦିତ ସୂଚନା; ପ୍ରକଳ୍ପର ଜ୍ଞାନଭଣ୍ଡାର ଦ୍ୱାରା ଯାଞ୍ଚ ହୋଇନାହିଁ।",
    "as": "বাহ্যিক, সম্প্ৰদায়-সম্পাদিত তথ্য; প্ৰকল্পৰ জ্ঞানভঁৰালে সত্যাপন কৰা নাই।",
}


def _terms(text: str) -> set[str]:
    return set(WORD_RE.findall((text or "").casefold()))


def _likely_duplicate(main_answer: str, source_text: str) -> bool:
    source_terms = _terms(source_text)
    if not source_terms:
        return True
    main_terms = _terms(main_answer)
    if not main_terms:
        return False
    return len(source_terms & main_terms) / len(source_terms) >= 0.72


def _possible_numeric_conflict(main_answer: str, summary: ExternalSummary) -> bool:
    main_values: dict[str, set[str]] = {}
    source_values: dict[str, set[str]] = {}
    for value, unit in MEASUREMENT_RE.findall(main_answer or ""):
        main_values.setdefault(unit.casefold().replace(" ", ""), set()).add(value)
    for value, unit in MEASUREMENT_RE.findall(summary.extract):
        source_values.setdefault(unit.casefold().replace(" ", ""), set()).add(value)
    shared_units = main_values.keys() & source_values.keys()
    return any(main_values[unit] != source_values[unit] for unit in shared_units)


def append_supplementary_summaries(
    main_answer: str,
    summaries: Sequence[ExternalSummary],
) -> tuple[str, list[dict]]:
    """Append only useful short summaries and return attributable external citations."""
    selected = [
        summary for summary in summaries[:2]
        if summary.extract.strip() and not _likely_duplicate(main_answer, summary.extract)
    ]
    if not selected:
        return main_answer, []

    language = (selected[0].language or "en").lower()
    lines = [
        f"### {ADDITIONAL_INFORMATION_LABELS.get(language, ADDITIONAL_INFORMATION_LABELS['en'])}",
        EXTERNAL_CONTEXT_LABELS.get(language, EXTERNAL_CONTEXT_LABELS["en"]),
    ]
    citations = []
    possible_conflict = any(_possible_numeric_conflict(main_answer, summary) for summary in selected)
    if possible_conflict:
        lines.append(
            "The sources include numerical values that have not been reconciled; they are kept separate."
        )
    for summary in selected:
        lines.append(summary.extract)
        citations.append({
            "source": summary.title,
            "url": summary.url,
            "source_type": "external",
            "license": summary.license,
            "retrieved_at": summary.retrieved_at,
            "page_timestamp": summary.page_timestamp,
            "cache_hit": summary.cache_hit,
        })
    return f"{main_answer.rstrip()}\n\n" + "\n\n".join(lines), citations
