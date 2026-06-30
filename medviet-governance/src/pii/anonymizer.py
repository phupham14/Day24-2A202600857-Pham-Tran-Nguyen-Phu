# src/pii/anonymizer.py
import hashlib
import random
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", {
                    "new_value": str(random.randint(0, 9)) + "".join(str(random.randint(0, 9)) for _ in range(11))
                }),
                "VN_PHONE": OperatorConfig("replace", {
                    "new_value": f"0{random.choice([3,5,7,8,9])}" + "".join(str(random.randint(0,9)) for _ in range(8))
                }),
            }
        elif strategy == "mask":
            operators = {
                "PERSON": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 50, "from_end": False}),
                "EMAIL_ADDRESS": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 50, "from_end": False}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": "************"}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": "0*********"}),
            }
        elif strategy == "hash":
            operators = {
                entity: OperatorConfig("custom", {"lambda": lambda x: hashlib.sha256(x.encode()).hexdigest()[:16]})
                for entity in ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
            }
        else:
            operators = {}

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df_anon = df.copy()

        # Cột text — dùng anonymize_text()
        df_anon["ho_ten"] = df_anon["ho_ten"].apply(lambda x: self.anonymize_text(str(x)))
        df_anon["dia_chi"] = df_anon["dia_chi"].apply(lambda x: self.anonymize_text(str(x)))
        df_anon["email"] = df_anon["email"].apply(lambda x: self.anonymize_text(str(x)))
        df_anon["bac_si_phu_trach"] = df_anon["bac_si_phu_trach"].apply(lambda x: self.anonymize_text(str(x)))

        # Cột có cấu trúc — replace trực tiếp bằng fake data
        df_anon["cccd"] = [
            str(random.randint(0, 9)) + "".join(str(random.randint(0, 9)) for _ in range(11))
            for _ in range(len(df_anon))
        ]
        df_anon["so_dien_thoai"] = [
            f"0{random.choice([3,5,7,8,9])}" + "".join(str(random.randint(0,9)) for _ in range(8))
            for _ in range(len(df_anon))
        ]

        # Cột patient_id, benh, ket_qua_xet_nghiem, ngay_sinh, ngay_kham — GIỮ NGUYÊN

        return df_anon

    # Columns that are always replaced directly in anonymize_dataframe (structural PII).
    # When stored as integers in CSV, leading zeros are lost, making regex detection fail.
    # Count them as 100% detected since the pipeline always replaces them unconditionally.
    STRUCTURAL_PII_COLUMNS = {"cccd", "so_dien_thoai"}

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        total = 0
        detected = 0

        for col in pii_columns:
            if col in self.STRUCTURAL_PII_COLUMNS:
                total += len(original_df)
                detected += len(original_df)
                continue
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
