"""
Generate an eligibility-assessment dataset for manifold-capacity analysis.

The prompt for this task lives outside the dataset JSON at:
    prompts/eligibility_system_prompt.txt

Tree structure (height 2):

                Final (Eligible)
               /                \\
    G1 (Financial Stability)    G2 (Credit Profile)
       /         \\                /           \\
  C1 (Age)   C2 (Income)   C3 (Credit)   C4 (Savings)

Evaluation order: C1, C2, G1, C3, C4, G2, Final
(post-order traversal: left subtree -> right subtree -> root)

Each leaf criterion: extract a number from prose, compare to threshold -> Met / Not Met
Each group node: combine children via AND or OR -> Met / Not Met
"""

import random
import json
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_PATH = SCRIPT_DIR / "data" / "eligibility_dataset.json"
PROMPT_PATH = SCRIPT_DIR / "prompts" / "eligibility_system_prompt.txt"


# ─────────────────────────────────────────────
# Demographic pools
# ─────────────────────────────────────────────

FIRST_NAMES_M = [
    "James", "David", "Michael", "Robert", "Daniel", "William", "Thomas",
    "Joseph", "Andrew", "Ryan", "Kevin", "Marcus", "Brian", "Stephen",
    "Carlos", "Ahmed", "Wei", "Hiroshi", "Omar", "Nikolai", "Mateo",
    "Patrick", "Samuel", "Vincent", "Derek", "Adrian", "Grant", "Leon",
    "Gregory", "Russell", "Howard", "Nathan", "Peter", "Dustin", "Travis",
]

FIRST_NAMES_F = [
    "Sarah", "Emily", "Jessica", "Maria", "Jennifer", "Rachel", "Amanda",
    "Sophia", "Olivia", "Elena", "Priya", "Mei", "Fatima", "Yuki", "Lena",
    "Catherine", "Diana", "Laura", "Karen", "Nicole", "Samantha", "Monica",
    "Angela", "Christine", "Heather", "Vanessa", "Tanya", "Rebecca", "Julia",
    "Hannah", "Chloe", "Audrey", "Natalie", "Allison", "Claire", "Brenda",
]

LAST_NAMES = [
    "Smith", "Johnson", "Chen", "Rodriguez", "Kim", "Patel", "Williams",
    "Brown", "Garcia", "Martinez", "Lee", "Taylor", "Anderson", "Thomas",
    "Jackson", "White", "Harris", "Thompson", "Robinson", "Walker",
    "Nguyen", "Tanaka", "Muller", "Johansson", "Okafor", "Russo", "Larsen",
    "Burke", "Reeves", "Sullivan", "Hoffman", "Fischer", "Mendez", "Blair",
    "Hawkins", "Barrett", "Fleming", "Chambers", "Ortiz", "Rivera",
]

OCCUPATIONS = [
    "software engineer", "teacher", "nurse", "accountant", "marketing manager",
    "mechanical engineer", "pharmacist", "graphic designer", "data analyst",
    "project manager", "sales representative", "research scientist",
    "civil engineer", "financial analyst", "human resources specialist",
    "physical therapist", "architect", "operations manager", "consultant",
    "technical writer", "social worker", "dentist", "journalist",
    "electrical engineer", "product manager", "veterinarian", "paralegal",
    "occupational therapist", "real estate agent", "supply chain analyst",
]

CITIES = [
    ("Portland", "Oregon"), ("Austin", "Texas"), ("Chicago", "Illinois"),
    ("Seattle", "Washington"), ("Denver", "Colorado"), ("Boston", "Massachusetts"),
    ("Phoenix", "Arizona"), ("Nashville", "Tennessee"), ("Raleigh", "North Carolina"),
    ("Minneapolis", "Minnesota"), ("San Diego", "California"), ("Tampa", "Florida"),
    ("Columbus", "Ohio"), ("Pittsburgh", "Pennsylvania"), ("Salt Lake City", "Utah"),
    ("Charlotte", "North Carolina"), ("Indianapolis", "Indiana"),
    ("Richmond", "Virginia"), ("Milwaukee", "Wisconsin"), ("Omaha", "Nebraska"),
    ("Boise", "Idaho"), ("Tucson", "Arizona"), ("Sacramento", "California"),
    ("Louisville", "Kentucky"), ("Albuquerque", "New Mexico"),
    ("Kansas City", "Missouri"), ("Spokane", "Washington"), ("Tulsa", "Oklahoma"),
]

EDUCATIONS = [
    "high school diploma", "associate's degree", "bachelor's degree",
    "master's degree", "professional degree",
]

EMPLOYER_TYPES = [
    "current employer", "current company", "present firm", "current position",
    "current organization",
]

HOUSING_TYPES = [
    "single-family home", "condominium", "townhouse", "apartment", "duplex",
]

# ─────────────────────────────────────────────
# Threshold pools (realistic "policy" values)
# ─────────────────────────────────────────────

AGE_THRESHOLDS = [25, 28, 30, 35, 40]
INCOME_THRESHOLDS = [50000, 60000, 70000, 75000, 80000, 85000, 90000, 100000]
CREDIT_THRESHOLDS = [640, 660, 680, 700, 720, 740]
SAVINGS_THRESHOLDS = [10000, 15000, 20000, 25000, 30000, 35000, 40000]


# ─────────────────────────────────────────────
# Tree label generation (balanced)
# ─────────────────────────────────────────────

def valid_inputs(op: str, desired: bool) -> list[tuple[bool, bool]]:
    """Return all (left, right) pairs such that left OP right == desired."""
    if op == "AND":
        return [(True, True)] if desired else [(True, False), (False, True), (False, False)]
    else:  # OR
        return [(True, True), (True, False), (False, True)] if desired else [(False, False)]


def generate_tree():
    """
    Generate random operators and balanced labels for the tree.
    Final label is forced to 50/50 across the dataset.
    """
    ops = {
        "G1": random.choice(["AND", "OR"]),
        "G2": random.choice(["AND", "OR"]),
        "Final": random.choice(["AND", "OR"]),
    }

    final = random.choice([True, False])
    g1, g2 = random.choice(valid_inputs(ops["Final"], final))
    c1, c2 = random.choice(valid_inputs(ops["G1"], g1))
    c3, c4 = random.choice(valid_inputs(ops["G2"], g2))

    labels = {"C1": c1, "C2": c2, "G1": g1, "C3": c3, "C4": c4, "G2": g2, "Final": final}
    return ops, labels


# ─────────────────────────────────────────────
# Attribute and threshold generation
# ─────────────────────────────────────────────

def make_value(threshold: int, should_meet: bool,
               offset_range: tuple[int, int], round_to: int = 1,
               floor: int = 1) -> int:
    """
    Generate a value that is above (should_meet=True) or below the threshold.
    Offset is drawn uniformly from offset_range, then result is rounded.
    """
    lo, hi = offset_range
    offset = random.randint(lo, hi)
    if should_meet:
        val = threshold + offset
    else:
        val = threshold - offset
        # Ensure the value is strictly below the threshold
        val = min(val, threshold - 1)
    val = round(val / round_to) * round_to
    return max(val, floor)


def generate_profile(labels: dict) -> tuple[dict, dict]:
    """
    Generate applicant attributes and policy thresholds.
    Attributes are designed to satisfy or violate thresholds per `labels`.
    """
    thresholds = {
        "age": random.choice(AGE_THRESHOLDS),
        "income": random.choice(INCOME_THRESHOLDS),
        "credit": random.choice(CREDIT_THRESHOLDS),
        "savings": random.choice(SAVINGS_THRESHOLDS),
    }

    attrs = {
        "age": make_value(thresholds["age"], labels["C1"],
                          (1, 8), round_to=1, floor=18),
        "income": make_value(thresholds["income"], labels["C2"],
                             (2000, 20000), round_to=1000, floor=20000),
        "credit": make_value(thresholds["credit"], labels["C3"],
                             (5, 50), round_to=1, floor=300),
        "savings": make_value(thresholds["savings"], labels["C4"],
                              (1000, 15000), round_to=500, floor=1000),
    }

    # Distractor attributes
    max_yrs = max(1, attrs["age"] - 20)
    attrs["years_employed"] = random.randint(1, min(25, max_yrs))
    attrs["dependents"] = random.randint(0, 4)
    attrs["education"] = random.choice(EDUCATIONS)

    return attrs, thresholds


def verify_labels(attrs: dict, thresholds: dict, ops: dict, labels: dict) -> bool:
    """Verify that the generated attributes match the expected labels."""
    c1 = attrs["age"] >= thresholds["age"]
    c2 = attrs["income"] >= thresholds["income"]
    c3 = attrs["credit"] >= thresholds["credit"]
    c4 = attrs["savings"] >= thresholds["savings"]

    if ops["G1"] == "AND":
        g1 = c1 and c2
    else:
        g1 = c1 or c2

    if ops["G2"] == "AND":
        g2 = c3 and c4
    else:
        g2 = c3 or c4

    if ops["Final"] == "AND":
        final = g1 and g2
    else:
        final = g1 or g2

    computed = {"C1": c1, "C2": c2, "G1": g1, "C3": c3, "C4": c4, "G2": g2, "Final": final}
    return computed == labels


# ─────────────────────────────────────────────
# Prose generation (varied templates)
# ─────────────────────────────────────────────

def format_money(amount: int) -> str:
    """Format an integer as $XX,XXX."""
    return f"${amount:,}"


def generate_prose(name: str, gender: str, occupation: str,
                   city: str, state: str, attrs: dict) -> str:
    """
    Generate a natural-language paragraph describing the applicant.
    Includes the 4 target attributes + 1-2 distractor attributes.
    Sentence order is partially shuffled to prevent positional shortcuts.
    """
    subj = "He" if gender == "M" else "She"
    poss = "His" if gender == "M" else "Her"
    subj_l = subj.lower()

    age = attrs["age"]
    income = format_money(attrs["income"])
    credit = attrs["credit"]
    savings = format_money(attrs["savings"])
    yrs = attrs["years_employed"]
    deps = attrs["dependents"]
    edu = attrs["education"]

    # ── Intro sentence (always first, always contains age) ──
    article = "an" if occupation[0].lower() in "aeiou" else "a"
    intro_pool = [
        f"{name} is a {age}-year-old {occupation} from {city}, {state}.",
        f"At {age} years old, {name} works as {article} {occupation} in {city}, {state}.",
        f"{name}, age {age}, is {article} {occupation} based in {city}, {state}.",
        f"{name} is a {age}-year-old {occupation} living in {city}, {state}.",
    ]

    # ── Attribute sentences (shuffled) ──
    income_pool = [
        f"{subj} earns {income} per year.",
        f"{poss} annual income is {income}.",
        f"{subj} makes {income} annually.",
        f"{subj} brings in {income} a year before taxes.",
    ]

    credit_pool = [
        f"{poss} credit score is {credit}.",
        f"{subj} has a credit score of {credit}.",
        f"A recent credit report shows a score of {credit}.",
        f"{poss} current credit score stands at {credit}.",
    ]

    savings_pool = [
        f"{subj} has {savings} in liquid savings.",
        f"{poss} liquid savings total {savings}.",
        f"Currently, {subj_l} holds {savings} in savings.",
        f"{subj} maintains {savings} in readily accessible savings.",
    ]

    # ── Distractor sentences (1-2 chosen) ──
    dep_word = "dependent" if deps == 1 else "dependents"
    distractor_pool = [
        f"{subj} has been with {poss.lower()} {random.choice(EMPLOYER_TYPES)} for {yrs} years.",
        f"{subj} has {deps} {dep_word}.",
        f"{subj} holds a {edu}.",
    ]
    housing = random.choice(HOUSING_TYPES)
    h_article = "an" if housing[0].lower() in "aeiou" else "a"
    distractor_pool.append(
        f"{subj} recently moved to {h_article} {housing} in the area."
    )

    intro = random.choice(intro_pool)
    income_s = random.choice(income_pool)
    credit_s = random.choice(credit_pool)
    savings_s = random.choice(savings_pool)
    distractors = random.sample(distractor_pool, k=random.randint(1, 2))

    # Shuffle the body sentences (attributes + distractors)
    body = [income_s, credit_s, savings_s] + distractors
    random.shuffle(body)

    return intro + " " + " ".join(body)


# ─────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────

def format_criteria_tree(thresholds: dict, ops: dict) -> str:
    """Format the criteria tree as it appears in the user message."""
    return (
        f"- C1 (Age): age ≥ {thresholds['age']}\n"
        f"- C2 (Income): income ≥ {format_money(thresholds['income'])}\n"
        f"- G1 (Financial Stability): C1 {ops['G1']} C2\n"
        f"- C3 (Credit Score): credit score ≥ {thresholds['credit']}\n"
        f"- C4 (Savings): savings ≥ {format_money(thresholds['savings'])}\n"
        f"- G2 (Credit Profile): C3 {ops['G2']} C4\n"
        f"- Final (Eligible): G1 {ops['Final']} G2"
    )


def format_user_message(prose: str, criteria_str: str) -> str:
    """Format the complete user message for one sample."""
    return (
        "Evaluate whether the following applicant meets the eligibility criteria.\n\n"
        f"**Applicant:**\n{prose}\n\n"
        f"**Criteria:**\n{criteria_str}"
    )


# ─────────────────────────────────────────────
# Sample generation
# ─────────────────────────────────────────────

def generate_sample(sample_id: int) -> dict:
    """Generate one complete sample with verified labels."""
    # Try up to 10 times to get a valid sample (should almost always succeed first try)
    for _ in range(10):
        ops, labels = generate_tree()
        attrs, thresholds = generate_profile(labels)
        if verify_labels(attrs, thresholds, ops, labels):
            break
    else:
        raise RuntimeError(f"Could not generate valid sample {sample_id} after 10 attempts")

    # Demographics
    gender = random.choice(["M", "F"])
    first = random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    occupation = random.choice(OCCUPATIONS)
    city, state = random.choice(CITIES)

    # Prose
    prose = generate_prose(name, gender, occupation, city, state, attrs)

    # Criteria tree string
    criteria_str = format_criteria_tree(thresholds, ops)

    # User message
    user_message = format_user_message(prose, criteria_str)

    return {
        "id": sample_id,
        "user_message": user_message,
        "labels": {k: bool(v) for k, v in labels.items()},
        "operators": ops,
        "attributes": {
            "age": attrs["age"],
            "income": attrs["income"],
            "credit": attrs["credit"],
            "savings": attrs["savings"],
        },
        "thresholds": thresholds,
        "name": name,
    }


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate eligibility assessment dataset")
    parser.add_argument("--num-samples", type=int, default=256,
                        help="Number of samples to generate (default: 256)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_PATH),
                        help="Output JSON file path")
    args = parser.parse_args()

    random.seed(args.seed)

    print(f"Generating {args.num_samples} samples with seed={args.seed}...")
    samples = []
    for i in range(args.num_samples):
        samples.append(generate_sample(i))

    # ── Label balance report ──
    NODE_IDS = ["C1", "C2", "G1", "C3", "C4", "G2", "Final"]
    print("\nLabel balance:")
    for node in NODE_IDS:
        true_ct = sum(1 for s in samples if s["labels"][node])
        pct = 100 * true_ct / len(samples)
        print(f"  {node:>5s}: {true_ct:>4d} Met / {len(samples) - true_ct:>4d} Not Met  ({pct:.1f}%)")

    # ── Operator distribution ──
    print("\nOperator distribution:")
    for group in ["G1", "G2", "Final"]:
        and_ct = sum(1 for s in samples if s["operators"][group] == "AND")
        print(f"  {group:>5s}: {and_ct} AND / {len(samples) - and_ct} OR")

    # ── Save ──
    output = {
        "metadata": {
            "task": "eligibility_assessment",
            "tree_height": 2,
            "num_samples": len(samples),
            "seed": args.seed,
            "node_ids": NODE_IDS,
            "evaluation_order": ["C1", "C2", "G1", "C3", "C4", "G2", "Final"],
            "structural_tokens": {
                "leaf_criterion": [
                    "**Criterion {id} ({name})**",
                    "* Extract:",
                    "* Threshold:",
                    "* Compare:",
                    "* Result:",
                ],
                "group_node": [
                    "**Group {id} ({name})**",
                    "* Logic:",
                    "* Result:",
                ],
                "final_node": [
                    "**Final (Eligible)**",
                    "* Logic:",
                    "* Result:",
                ],
                "summary": [
                    "### Summary",
                    "* C1:", "* C2:", "* G1:",
                    "* C3:", "* C4:", "* G2:",
                    "* Final:",
                ],
            },
        },
        "samples": samples,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {out_path}")
    print(f"  System prompt file: {PROMPT_PATH}")

    # ── Print one example ──
    print("\n" + "=" * 60)
    print("EXAMPLE SAMPLE (id=0)")
    print("=" * 60)
    ex = samples[0]
    print(f"\nLabels: {ex['labels']}")
    print(f"Operators: {ex['operators']}")
    print(f"\n--- User message ---\n{ex['user_message']}")


if __name__ == "__main__":
    main()
