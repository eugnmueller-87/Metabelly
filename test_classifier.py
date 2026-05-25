"""
Quick test of the triage classifier against real Metabelly customer questions.
Run: python test_classifier.py
Requires MISTRAL_API_KEY in .env
"""

import asyncio

from dotenv import load_dotenv

load_dotenv()

from metabelly.agents.classifier import TriageClassifier

# Real questions sampled from the HubSpot chat PDF
TEST_CASES = [
    {
        "label": "FAQ - ingredients",
        "message": "Koji je sastav metabelly fiber?",
    },
    {
        "label": "FAQ - children dosage",
        "message": "Mogu li i djeca uzimati fiber vlakna i da li je doziranje isto kao i za odrasle? Djeca imaju 5 i 8 godina.",
    },
    {
        "label": "FAQ - delivery",
        "message": "Dobar dan, zelim naruciti FIBER vlakna za Pulu. Koliko dugo se ceka?",
    },
    {
        "label": "MEDICAL - IBS/FODMAP",
        "message": "Imam jak IBS, jedem prema fodmapu godinama no unatoc strogoj disciplini (bez glutena, laktoze, skrobova, fruktoze) i dalje imam proljeve 3-4 puta dnevno.",
    },
    {
        "label": "MEDICAL - cancer patient",
        "message": "Ja sam liječeni onkološki bolesnik (karcinom dojke) i na višegodišnjoj sam terapiji inhibitorom aromataze. Postoji li neka kontraindikacija za korištenje fibera?",
    },
    {
        "label": "MEDICAL - Crohn's disease",
        "message": "Naručila sam fiber vrećice, a bolujem od Crohnove bolesti. Bojim se da to meni neće pomoći.",
    },
    {
        "label": "ORDER - coupon not working",
        "message": "Naručujem vlakna i idem iskoristit welcome 10 zasto nece da prihvati",
    },
    {
        "label": "ORDER - payment issue",
        "message": "Tražila sam uplatni račun i jednostavan način plaćanja. To mi je još nepoznanica.",
    },
    {
        "label": "BUSINESS - Serbia market",
        "message": "poslujete li u srbiji?",
    },
    {
        "label": "BUSINESS - microbiome analysis",
        "message": "Zanima me kako se ostvaruje popust od 10% prilikom prijave? I može li se napraviti analiza mikrobioma za dijete od 7,5 godina?",
    },
    {
        "label": "MEDICAL - urgent/distress",
        "message": "Bol me u donjem lijevom dijelu trbuha već tjednima, nadutost je strašna, nema stolice danima. Ginekološki sve ok. Ne znam što više napraviti.",
    },
    {
        "label": "FAQ - English",
        "message": "Is your product safe for people with celiac disease? Thank you",
    },
]


async def run_tests():
    classifier = TriageClassifier()

    print("=" * 70)
    print("METABELLY TRIAGE CLASSIFIER TEST")
    print("=" * 70)

    for case in TEST_CASES:
        print(f"\n[{case['label']}]")
        print(f"Input: {case['message'][:80]}{'...' if len(case['message']) > 80 else ''}")

        result = classifier.classify(case["message"])

        print(f"Category:  {result.category.value.upper()}")
        print(f"Priority:  {result.priority.value}")
        print(f"Language:  {result.language.value}")
        print(f"Summary:   {result.summary}")
        print(f"Human?:    {result.requires_human}")
        print(f"Action:    {result.suggested_action}")

        if result.auto_reply:
            preview = result.auto_reply[:120].encode("utf-8", errors="replace").decode("utf-8")
            print(f"Auto-reply preview: {preview}...")

        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(run_tests())
