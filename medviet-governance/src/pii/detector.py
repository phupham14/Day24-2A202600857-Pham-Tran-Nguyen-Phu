# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
import spacy

VI_LANGUAGE = "vi"
SUPPORTED_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
VI_MODEL_CANDIDATES = ("vi_spacy_model", "vi_core_news_lg")


def _resolve_vi_model_name() -> str:
    for name in VI_MODEL_CANDIDATES:
        try:
            spacy.load(name)
            return name
        except OSError:
            continue
    return ""


def build_vietnamese_analyzer() -> AnalyzerEngine:
    # --- TASK 2.2.1 ---
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"\b\d{12}\b",
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language=VI_LANGUAGE,
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 ---
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(
            name="vn_phone",
            regex=r"\b0[35789]\d{8}\b",
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(
            name="email_pattern",
            regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            score=0.9,
        )],
        context=["email", "mail", "gmail"],
    )

    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(
            name="vn_person_latin",
            regex=(
                r"\b[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
                r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]*"
                r"(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ"
                r"a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+){0,3}\b"
            ),
            score=0.65,
        )],
    )

    # --- TASK 2.2.3 ---
    model_name = _resolve_vi_model_name()
    if model_name:
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": VI_LANGUAGE, "model_name": model_name}],
        }
    else:
        # Fallback: blank spaCy model — pattern recognizers vẫn hoạt động đầy đủ
        import tempfile, pathlib
        blank_path = pathlib.Path(tempfile.gettempdir()) / "vi_blank"
        if not blank_path.exists():
            spacy.blank("vi").to_disk(blank_path)
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": VI_LANGUAGE, "model_name": str(blank_path)}],
        }

    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

    # --- TASK 2.2.4 ---
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[VI_LANGUAGE])
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)
    analyzer.registry.add_recognizer(person_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    results = analyzer.analyze(
        text=text,
        language=VI_LANGUAGE,
        entities=SUPPORTED_ENTITIES,
    )
    return results
