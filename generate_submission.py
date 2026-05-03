import json
import os
from typing import Dict, Any, List
from composer import Composer, ContextStore


def load_json(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_submission():
    composer = Composer()

    category_path = "dataset/categories/dentists.json"
    merchant_path = "dataset/merchants/m_001_drmeera_dentist_delhi.json"
    trigger_path = "dataset/triggers/trg_001_research_digest_dentists.json"

    category_data = load_json(category_path)
    merchant_data = load_json(merchant_path)
    trigger_data = load_json(trigger_path)

    composer.store.store_context("category", "dentists", 1, category_data)
    composer.store.store_context("merchant", "m_001_drmeera_dentist_delhi", 1, merchant_data)
    composer.store.store_context("trigger", "trg_001_research_digest_dentists", 1, trigger_data)

    category = composer.store.get_category("dentists")
    merchant = composer.store.get_merchant("m_001_drmeera_dentist_delhi")
    trigger = composer.store.get_trigger("trg_001_research_digest_dentists")

    if not all([category, merchant, trigger]):
        print("Error: Failed to load contexts")
        return

    message = composer.compose(category, merchant, trigger, None)

    submission_entry = {
        "test_id": "T01",
        "body": message.body,
        "cta": message.cta,
        "send_as": message.send_as,
        "suppression_key": message.suppression_key,
        "rationale": message.rationale
    }

    with open("submission.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps(submission_entry) + "\n")

    print("✅ Submission generated successfully!")
    print(f"\nTest ID: {submission_entry['test_id']}")
    print(f"Message Body:\n{submission_entry['body']}\n")
    print(f"CTA: {submission_entry['cta']}")
    print(f"Send As: {submission_entry['send_as']}")
    print(f"Rationale: {submission_entry['rationale']}")


if __name__ == "__main__":
    generate_submission()
