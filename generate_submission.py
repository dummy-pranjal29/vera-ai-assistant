import json
import os
from pathlib import Path
from dotenv import load_dotenv
from composer import Composer

load_dotenv()


def load_json(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_all_submissions():
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in .env file")
        print("Please add your API key to .env file")
        return

    print("Generating submission.jsonl for all 30 test cases...")
    print("=" * 60)

    composer = Composer()
    expanded_dir = Path("expanded")

    test_pairs = load_json(expanded_dir / "test_pairs.json")["pairs"]

    print(f"Found {len(test_pairs)} test pairs")

    categories_cache = {}

    submission_entries = []

    for i, pair in enumerate(test_pairs, 1):
        test_id = pair["test_id"]
        trigger_id = pair["trigger_id"]
        merchant_id = pair["merchant_id"]
        customer_id = pair.get("customer_id")

        print(f"\n[{i}/{len(test_pairs)}] Processing {test_id}: {merchant_id}")

        try:
            trigger_path = expanded_dir / "triggers" / f"{trigger_id}.json"
            merchant_path = expanded_dir / "merchants" / f"{merchant_id}.json"

            trigger_data = load_json(trigger_path)
            merchant_data = load_json(merchant_path)

            category_slug = merchant_data.get("category_slug")
            if not category_slug:
                print(f"  WARNING: No category_slug in merchant data, skipping")
                continue

            if category_slug not in categories_cache:
                category_path = expanded_dir / "categories" / f"{category_slug}.json"
                if category_path.exists():
                    categories_cache[category_slug] = load_json(category_path)
                else:
                    print(f"  WARNING: Category {category_slug} not found, skipping")
                    continue

            category_data = categories_cache[category_slug]

            composer.store.store_context("category", category_slug, 1, category_data)
            composer.store.store_context("merchant", merchant_id, 1, merchant_data)
            composer.store.store_context("trigger", trigger_id, 1, trigger_data)

            customer = None
            if customer_id:
                customer_path = expanded_dir / "customers" / f"{customer_id}.json"
                if customer_path.exists():
                    customer_data = load_json(customer_path)
                    composer.store.store_context("customer", customer_id, 1, customer_data)
                    customer = composer.store.get_customer(customer_id)

            category = composer.store.get_category(category_slug)
            merchant = composer.store.get_merchant(merchant_id)
            trigger = composer.store.get_trigger(trigger_id)

            print(f"  Composing message...")
            message = composer.compose(category, merchant, trigger, customer)

            submission_entry = {
                "test_id": test_id,
                "body": message.body,
                "cta": message.cta,
                "send_as": message.send_as,
                "suppression_key": message.suppression_key,
                "rationale": message.rationale
            }

            submission_entries.append(submission_entry)

            print(f"  Success")
            print(f"  Preview: {message.body[:80]}...")

        except Exception as e:
            print(f"  Error: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    with open("submission.jsonl", "w", encoding="utf-8") as f:
        for entry in submission_entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("\n" + "=" * 60)
    print(f"Generated {len(submission_entries)} messages")
    print(f"Saved to submission.jsonl")
    print("\nSample entry:")
    if submission_entries:
        print(json.dumps(submission_entries[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    generate_all_submissions()
