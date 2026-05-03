import json
import os
from dotenv import load_dotenv
from composer import Composer

load_dotenv()

def test_composition():
    print("Testing Vera AI Assistant...")
    print("=" * 60)

    composer = Composer()

    category_data = json.load(open("expanded/categories/dentists.json", "r", encoding="utf-8"))
    merchant_data = json.load(open("expanded/merchants/m_001_drmeera_dentist_delhi.json", "r", encoding="utf-8"))
    trigger_data = json.load(open("expanded/triggers/trg_001_research_digest_m_001_drmeera_dent.json", "r", encoding="utf-8"))

    composer.store.store_context("category", "dentists", 1, category_data)
    composer.store.store_context("merchant", "m_001_drmeera_dentist_delhi", 1, merchant_data)
    composer.store.store_context("trigger", "trg_001_research_digest_dentists", 1, trigger_data)

    category = composer.store.get_category("dentists")
    merchant = composer.store.get_merchant("m_001_drmeera_dentist_delhi")
    trigger = composer.store.get_trigger("trg_001_research_digest_dentists")

    print("\nContexts loaded:")
    print(f"  Category: {category.slug}")
    print(f"  Merchant: {merchant.identity.name}")
    print(f"  Trigger: {trigger.kind}")
    print("\nComposing message...")
    print("-" * 60)

    try:
        message = composer.compose(category, merchant, trigger, None)

        print("\nCOMPOSED MESSAGE:")
        print("=" * 60)
        print(message.body)
        print("=" * 60)
        print(f"\nCTA: {message.cta}")
        print(f"Send As: {message.send_as}")
        print(f"Suppression Key: {message.suppression_key}")
        print(f"\nRationale: {message.rationale}")
        print("\nTest PASSED!")

        return message

    except Exception as e:
        print(f"\nTest FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not found in .env file")
        print("Please add your API key to .env file")
        exit(1)

    test_composition()
