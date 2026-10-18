"""
Data ingestion module.
Loads raw IT Support Ticket datasets or generates a validated bootstrap dataset
if Kaggle raw files are not yet manually downloaded, ensuring pipeline testability.
"""

import random
from pathlib import Path

import pandas as pd

DATA_RAW_DIR = Path("data/raw")
ROUTING_RAW_FILE = DATA_RAW_DIR / "ticket_routing.csv"
PRIORITY_RAW_FILE = DATA_RAW_DIR / "ticket_priority.csv"

# Seed data templates for realistic enterprise bootstrap
CATEGORIES_TEMPLATES = {
    "Access": [
        "Need access to database server for production migration.",
        "Password reset required for Active Directory account.",
        "VPN connection timed out, unable to reach internal network.",
        "Cannot login to AWS console, getting 403 Forbidden.",
        "Please unlock my domain account after multiple failed attempts.",
        "Requesting MFA reset on my registered mobile device.",
        "Permission denied accessing shared network folder.",
        "SSO session expired and Okta authentication loop occurs.",
    ],
    "Administrative rights": [
        "Requesting local administrator rights to install developer tools.",
        "Need admin privileges to install python and nodejs on my workstation.",
        "Permission required to edit hostfile and network adapters.",
        "Need elevated access to update internal security certificates.",
        "Requesting sudo privileges on Linux staging bastion server.",
        "Grant admin access to run Docker Desktop daemon.",
        "Install proprietary engineering software requiring UAC elevation.",
        "Enable developer mode and admin rights on Windows 11 laptop.",
    ],
    "HR Support": [
        "How do I update my bank account details in payroll portal?",
        "Where can I find the maternity and paternity leave policy?",
        "Expense claim was rejected without reason in HR system.",
        "Requesting employment verification letter for visa application.",
        "Questions regarding health insurance dental coverage enrolment.",
        "Annual performance appraisal self-assessment form issue.",
        "Need assistance with updating emergency contact information.",
        "Query regarding accrued paid time off balance discrepancy.",
    ],
    "Hardware": [
        "Laptop will not turn on and charging LED is not blinking.",
        "Screen flickers constantly when plugged into docking station.",
        "Trackpad on MacBook Pro is unresponsive and battery appears swollen.",
        "External monitor displays no signal through HDMI cable.",
        "Mechanical keyboard keys repeating and spacebar stuck.",
        "Headset microphone produces static noise during Zoom calls.",
        "Replacement power supply adapter needed for Lenovo ThinkPad.",
        "Printer on 3rd floor paper jam error not clearing.",
    ],
    "Internal Project": [
        "Git repository creation request for project Phoenix.",
        "Configure GitLab CI runner on dedicated build machine.",
        "Need SonarQube quality gate configured for sprint release.",
        "Jira board permissions for new team joiners in project Apollo.",
        "Requesting staging Kubernetes cluster namespace allocation.",
        "Confluence space creation for technical architecture specs.",
        "Setup internal Artifactory repository for private Python wheels.",
        "Database schema migration script failing in sandbox environment.",
    ],
    "Miscellaneous": [
        "Where can I request extra coffee cups and stationery for office?",
        "Office temperature is too cold on the east wing.",
        "Car parking access card is not recognized at garage gate.",
        "Lost and found inquiry for sunglasses left in cafeteria.",
        "Meeting room projector lamp burned out in conference room B.",
        "Requesting desk cleaning service after renovation work.",
        "Where do I submit company feedback suggestions?",
        "Water dispenser on 2nd floor is leaking.",
    ],
    "Purchase": [
        "Request purchase order for 10 JetBrains DataGrip licenses.",
        "Order replacement ergonomic chair for software engineer.",
        "Need purchase approval for AWS cloud training certifications.",
        "Procurement of 27-inch 4K dual monitors for design team.",
        "Invoice approval for annual Datadog monitoring subscription.",
        "Order 5 YubiKey hardware security tokens for DevOps team.",
        "Purchase request for standing desk converter.",
        "Procurement of noise-canceling headphones for open floor.",
    ],
    "Storage": [
        "Shared network drive full, cannot save project files.",
        "Requesting 500GB additional storage on NAS volume.",
        "Increase AWS S3 bucket quota for model training artifacts.",
        "Backup recovery request for deleted directory on file server.",
        "Cloud storage synchronization client stuck at 99%.",
        "Permission to mount NFS export on analytics compute cluster.",
        "Archive cold logs to Glacier storage to free disk space.",
        "Disk space critical warning on server /var/log partition.",
    ],
}

PRIORITY_LEVELS = ["Low", "Medium", "High", "Critical"]


def generate_bootstrap_data(num_samples: int = 1600) -> pd.DataFrame:
    """Generates synthetic, balanced, realistic tickets across categories."""
    random.seed(42)
    records = []
    cats = list(CATEGORIES_TEMPLATES.keys())
    per_cat = num_samples // len(cats)

    for cat in cats:
        templates = CATEGORIES_TEMPLATES[cat]
        for _i in range(per_cat):
            base = random.choice(templates)
            # Add subtle variations
            prefix = random.choice(
                ["Hi team, ", "Urgent: ", "Request: ", "Issue reported: ", "", "Please help: "]
            )
            suffix = random.choice(
                [" Thanks.", " Appreciate quick help.", " ASAP.", " Need this resolved today.", ""]
            )
            text = f"{prefix}{base}{suffix}".strip()

            # Assign priority with realistic distribution
            if any(k in text.lower() for k in ["urgent", "asap", "critical", "outage", "swollen"]):
                priority = random.choice(["High", "Critical"])
            elif cat in ["Hardware", "Access"]:
                priority = random.choice(["Medium", "High"])
            else:
                priority = random.choice(["Low", "Medium"])

            records.append(
                {
                    "ticket_id": f"TKT-{len(records) + 1:06d}",
                    "text": text,
                    "category": cat,
                    "priority": priority,
                }
            )

    random.shuffle(records)
    return pd.DataFrame(records)


def ingest_data():
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    if not ROUTING_RAW_FILE.exists():
        print(f"Raw routing data not found at {ROUTING_RAW_FILE}. Generating bootstrap dataset...")
        df = generate_bootstrap_data(num_samples=2400)
        df.to_csv(ROUTING_RAW_FILE, index=False)
        print(f"Generated and saved {len(df)} records to {ROUTING_RAW_FILE}.")
    else:
        print(f"Existing raw routing data found at {ROUTING_RAW_FILE}.")

    df = pd.read_csv(ROUTING_RAW_FILE)
    print(f"Ingestion verified. Total records: {len(df)}. Category distribution:")
    print(df["category"].value_counts())


if __name__ == "__main__":
    ingest_data()
