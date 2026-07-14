#!/usr/bin/env python3
"""Review independent silver-label passes without calling any model."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

import create_silver_labels as silver


INPUT = Path("redaction_reviewed_v5_clean.xlsx")
TAXONOMY = Path("../app/data/taxonomy_detailed_descriptions.csv")
REVIEW_DIR = Path("silver_labels/04_review")
OUTPUT = REVIEW_DIR / "redaction_reviewed_v5_clean_ai_silver_reviewed.xlsx"
MODELS = {
    "gpt52": Path(".silver_classification_checkpoint.json"),
    "gemini31_pro": Path("silver_labels/02_gemini31_pro/checkpoint.json"),
    "deepseek_v4": Path("silver_labels/03_deepseek_v4/checkpoint.json"),
}


# These are the decisions made in the in-context review for non-majority or
# especially ambiguous rows.  All other rows use a two/three-model consensus.
# The note is stored in final_review.json and in the workbook.
MANUAL: dict[int, tuple[str, str, str]] = {
    12: ("Labor & Employment", "Wage and Hour Claims", "The deleted hours are the concrete claim; termination is a secondary possible retaliation issue."),
    22: ("Debtor/Creditor", "Debt Counseling/Workouts", "The caller is trying to settle an acknowledged debt and obtain affordable payment terms."),
    24: ("General Litigation", "Wrongful Death", "The mother died after the fall, and the caller expressly seeks a wrongful-death remedy; medical malpractice is a possible underlying theory."),
    27: ("Labor & Employment", "Wrongful Discharge", "The only stated facts identify possible termination; discrimination is not tied to a protected characteristic."),
    31: ("Wills & Trusts", "Litigation", "The stated fiduciary-duty breach and limitations question indicate a dispute involving a trustee, not merely general elder planning."),
    46: ("Bankruptcy", "Other", "The caller is protecting assets from an ex-spouse's Chapter 7 and possible liability under a divorce decree, not collecting a debt owed by the debtor."),
    54: ("Labor & Employment", "Discrimination", "Discrimination in hiring and pay is the substantive dispute; union handling is a secondary route or context."),
    56: ("Wills & Trusts", "Power of Attorney", "The caller already holds POA and asks what that authority permits for the father's finances; guardianship may be a next step."),
    62: ("General Litigation", "Animal Law", "The injury is a dog-bite claim, and the detailed taxonomy treats animal-related disputes as Animal Law even when damages are physical."),
    70: ("General Litigation", "Neighbor Disputes/Nuisance", "The ongoing conduct is a broad neighbor/property nuisance dispute; a stalking order is a possible additional remedy."),
    76: ("Intellectual Property", "Patent (Reg Patent Attys Only)", "The user expressly asks about software patent categories and patent-protection strategy."),
    101: ("Bankruptcy", "Pro Se Coaching", "The request is general guidance about filing, without facts establishing a particular chapter or document-review need."),
    103: ("Bankruptcy", "Pro Se Coaching", "The caller wants help navigating a filing and has no money for counsel, matching pro se process coaching."),
    107: ("Bankruptcy", "Pro Se Coaching", "The caller asks whether they can file on their own or obtain reduced-fee guidance, which is coaching rather than a chapter-specific label."),
    116: ("Bankruptcy", "Other", "The issue is an ex-spouse's bankruptcy and possible liability under the divorce decree, not a creditor seeking repayment from the bankruptcy estate."),
    128: ("Business & Corporate", "Litigation", "A business-sale security is in foreclosure after nonpayment and unanswered notices; this is an enforcement dispute, not a new sale transaction or ordinary real-estate mortgage."),
    133: ("Business & Corporate", "Sale of Business", "The requested bill-of-sale review concerns transferring a business and its website/domain assets."),
    141: ("Business & Corporate", "General (Contracts, Business, Organization)", "Setting up an ownership group for a sports team is business organization, not an artist/creative-work contract."),
    155: ("Consumer Law", "General", "The dispute is primarily with a service provider over defective workmanship and failure to deliver a usable custom product, rather than a dealership vehicle purchase."),
    168: ("Consumer Law", "Automobiles/RVs/Mobile Homes", "The dispute centers on a financed Toyota purchase and title handling by a dealership."),
    172: ("Criminal Law", "Other", "Failure-to-register is a specialized criminal defense issue; the caller is not seeking removal from the registry, so Relief From Sex Offender Registration is not exact."),
    178: ("Criminal Law", "Major Felony", "The stated controlled-substance manufacturing/distribution charge is the central immediate criminal charge; probation revocation is secondary."),
    189: ("Criminal Law", "Other", "The sparse description involves an outstanding warrant and repeated arrests without a clearly identified charge or appeal posture."),
    196: ("Criminal Law", "Misdemeanor", "The caller expressly says the four charges are misdemeanors, even though the alleged conduct includes serious accusations."),
    198: ("Criminal Law", "Major Felony", "Sex Abuse I is a serious current criminal charge; the prior PCR history does not turn the present request into a post-conviction appeal."),
    202: ("Debtor/Creditor", "Debt Counseling/Workouts", "The caller acknowledges the debt, wants to pay, and asks for a workable remedy while keeping employment."),
    204: ("Debtor/Creditor", "Debt Counseling/Workouts", "The explicit goal is an affordable payment agreement with the bank."),
    206: ("Debtor/Creditor", "General (Debtor)", "The concrete problem is wage and bank-account garnishment; the text does not establish abusive collection conduct."),
    211: ("Debtor/Creditor", "General (Debtor)", "The caller needs to answer or file a motion concerning an existing debt and possible garnishment; a payment plan is secondary."),
    212: ("Debtor/Creditor", "Debt Counseling/Workouts", "The caller seeks to reduce or restructure a debt after a car accident, specifically asking about payment options."),
    233: ("Family Law", "Child Custody/Visitation", "Safety-plan, CPS, and parenting-time disputes make custody/visitation the central family-law routing issue, with support modification also present."),
    240: ("Family Law", "Restraining Orders", "The requested first remedy is dismissal of an existing restraining order; custody is a related second issue."),
    246: ("Family Law", "Juvenile/DHS Issue - SCF (CSD) related", "The dispute centers on CPS/DHS reports and efforts affecting whether the children remain with the parent."),
    252: ("Family Law", "General (Divorce/Separation)", "The caller expressly seeks a divorce or annulment; military and immigration facts are important context but not the requested legal matter."),
    255: ("General Litigation", "Civil Rights", "The caller wants a civil suit for allegedly unconstitutional extra imprisonment, which is a civil-rights damages claim."),
    266: ("General Litigation", "Animal Law", "This is a dog-bite injury; Animal Law is the detailed taxonomy's specific fit, with personal injury as a possible secondary framing."),
    273: ("General Litigation", "Malpractice-Medical", "The request says medical/dental malpractice involving a minor but does not identify a dental provider; medical malpractice is the broader supported match."),
    280: ("Intellectual Property", "Trademark/Copyright", "The writer asks about copyright and IP for books, brands, and licensing; the asset-trust question is secondary."),
    306: ("International Law", "Other", "The detailed taxonomy explicitly places political asylum cases in International Law/Other."),
    307: ("International Law", "Gen. Immigration/Visas", "The family wants help navigating immigration to Canada, which is general immigration/visa assistance."),
    329: ("Labor & Employment", "Discrimination", "Discrimination in hiring and pay is the stated employment injury; union problems are a secondary procedural context."),
    338: ("Labor & Employment", "Wrongful Discharge", "The caller challenges being laid off and alleges inconsistent treatment, making termination the central issue."),
    349: ("Workers' Comp", "State", "The text describes a workplace slip-and-fall with an existing workers-compensation claim and no identified third-party defendant."),
    356: ("Workers' Comp", "Other", "The request is for forms, document review, and cross-state legal advice, a specialized workers-comp need rather than a stated benefits denial."),
    370: ("Real Property", "Water Law", "The caller specifically needs to determine water rights and an easement to a water pipe; the purchase dispute is secondary."),
    374: ("Real Property", "Mobile Home (Tenant/Owner)", "The family rents a space in an RV/mobile-home park and was evicted after a park incident, fitting the specialized park-tenancy label."),
    384: ("Wills & Trusts", "Living Trusts", "The question is whether to transfer property into a trust, a specific living-trust planning decision."),
    402: ("Wills & Trusts", "Living Trusts", "The caller wants to set up a trust for financial assets and real estate, which is the specific living-trust label."),
    429: ("Administrative Law", "Schools - Special Needs Edu.", "The text connects mental-health-related behavior to trouble at school; special-needs educational support is the closer detailed description."),
    430: ("General Litigation", "Stalking Orders", "A car repeatedly following the caller is the clearest actionable issue and fits a stalking order; the media complaint is secondary."),
    4: ("Real Property", "Construction/Contractors", "The caller is a construction contractor seeking payment and a construction lien, matching the property-project description."),
    29: ("Real Property", "Construction/Contractors", "A homeowner paid a roofer that failed to perform; this is a specific construction-contractor dispute."),
    33: ("Bankruptcy", "Business", "The LLC has business debts and is likely filing bankruptcy as an entity; dissolution is related business context."),
    34: ("Real Property", "Agriculture/Farm", "The disputed verbal extension is an agricultural land lease, which the detailed guide places under real-property farm issues."),
    59: ("Real Property", "Construction/Contractors", "The homeowner disputes defective work and lien risk on a renovation project, rather than seeking generic small-claims coaching."),
    63: ("General Litigation", "Insurance (Health/Disability)", "The initially approved private disability claim was denied; this is the detailed guide's direct example of a private disability-coverage dispute."),
    96: ("Administrative Law", "SSD (Social Security Disability)", "The benefits are derivative of a parent's SSDI and the requested lawyer is specifically for Social Security benefits."),
    111: ("Debtor/Creditor", "General (Debtor)", "The caller is being sued by a creditor and is considering settlement or a motion; bankruptcy is only one possible option."),
    120: ("Real Property", "Construction/Contractors", "The requested remedy is construction-lien filing for unpaid contractor invoices, a specific property-project issue."),
    126: ("Intellectual Property", "Entertainment", "Royalty questions concern rights and monetization of performing works; the detailed IP/Entertainment description is more specific than nonprofit organization status."),
    130: ("Real Property", "Agriculture/Farm", "The disputed verbal extension is an agricultural land lease, matching the detailed real-property farm description."),
    136: ("Business & Corporate", "Securities", "Churning by a financial adviser is an investment/securities dispute and the caller expressly requests a securities lawyer."),
    137: ("Business & Corporate", "Securities", "Employee stock options and prepaid variable forwards are securities/financial instruments, not ordinary employment documents."),
    140: ("Real Property", "Agriculture/Farm", "The request specifically includes farm leases and transactions involving the farm property; Real Property/Agriculture is the more specific route."),
    152: ("Consumer Law", "General", "The caller is a consumer suing an auto-repair service over negligent, defective work; the detailed Consumer Law/General description directly covers faulty services."),
    213: ("Debtor/Creditor", "General (Debtor)", "The immediate issue is an alleged overpayment being sent to collections; the caller is being pursued as a debtor, without enough facts to call the collection abusive."),
    215: ("Consumer Law", "Problems Between Consumers", "The boat contract is described as a private transaction with a friend's acquaintance, not a dealership or business seller."),
    248: ("Administrative Law", "General (State)", "Correcting a state-issued Idaho birth certificate is the detailed guide's example of a state administrative issue."),
    305: ("International Law", "Gen. Immigration/Visas", "The requested help is recovering immigration documents; Social Security is the destination for the documents, not the disputed benefit."),
    330: ("Business & Corporate", "General (Contracts, Business, Organization)", "An employer-side consultation about terminating an employee is a business-operation question in this taxonomy, not an employee's discharge claim."),
    404: ("Administrative Law", "Medicare/Medicaid", "The parents received notice that Medicaid will terminate because of an asset; the detailed guide distinguishes benefit denials/terminations from Medicaid planning."),
    417: ("Real Property", "Tenant (Residential)", "The explicit housing remedy is eviction, which is a residential tenant issue; the criminal facts are not sufficiently specified."),
    420: ("Workers' Comp", "State", "The caller broke a foot at work; workers-compensation is the direct injury-benefits route, while firing and deportation are secondary questions."),
    421: ("General Litigation", "Personal Injury", "The clearest direct claim is compensation for being hit by a car; guardianship/beneficiary and parking-ticket issues are secondary."),
    422: ("Family Law", "Restraining Orders", "Repeated unwanted calls and fear of harm from a former intimate partner fit a family-law restraining order; the license issue is secondary."),
    424: ("Wills & Trusts", "General (Wills, Trusts, Estates)", "The caller expressly says they want to write a will; veteran benefits and nursing-licensing issues are separate matters."),
    426: ("Business & Corporate", "General (Contracts, Business, Organization)", "A provider business is contesting termination of its CareOregon contract; it seeks contract/appeal advice before a lawsuit is identified."),
}


def excel_col(number: int) -> str:
    result = ""
    while number:
        number, remainder = divmod(number - 1, 26)
        result = chr(65 + remainder) + result
    return result


def load_results() -> tuple[list[dict[str, str]], dict[str, dict[int, list[dict[str, str]]]]]:
    rows = silver.read_workbook_rows(INPUT)
    results = {
        name: {int(k): v for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
        for name, path in MODELS.items()
    }
    if any(len(value) != len(rows) - 1 for value in results.values()):
        raise ValueError("not all model checkpoints contain every input row")
    return rows, results


def choose_review(row_id: int, results: dict[str, dict[int, list[dict[str, str]]]]) -> tuple[dict[str, str], str]:
    candidates = [results[name][row_id][0] for name in MODELS]
    pairs = [(x["category"], x["subcategory"]) for x in candidates]
    if row_id in MANUAL:
        category, subcategory, note = MANUAL[row_id]
        return {
            "category": category,
            "subcategory": subcategory,
            "justification": note,
            "confidence": "reviewed",
        }, "in-context manual review"
    winner, count = Counter(pairs).most_common(1)[0]
    selected = next(x for x in candidates if (x["category"], x["subcategory"]) == winner)
    basis = "three-model consensus" if count == 3 else "two-model consensus"
    return {
        "category": selected["category"],
        "subcategory": selected["subcategory"],
        "justification": selected["justification"] + f" Reviewed as {basis}.",
        "confidence": "reviewed",
    }, basis


def write_review_json(rows: list[dict[str, str]], results: dict[str, dict[int, list[dict[str, str]]]]) -> dict[int, dict[str, str]]:
    reviewed: dict[int, dict[str, str]] = {}
    audit: dict[str, object] = {
        "review_method": "No API call. Rank-1 model outputs were compared; unanimous rows use three-model consensus, two-agreement rows use two-model consensus, and listed ambiguous rows were reviewed in context against the detailed taxonomy.",
        "models": list(MODELS),
        "rows": {},
    }
    for row_id in range(2, len(rows) + 1):
        review, basis = choose_review(row_id, results)
        reviewed[row_id] = review
        audit["rows"][str(row_id)] = {
            "problem_description": rows[row_id - 1]["A"],
            "models": {name: results[name][row_id] for name in MODELS},
            "review": review,
            "basis": basis,
        }
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    (REVIEW_DIR / "final_review.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    return reviewed


def set_cell(row: ET.Element, col: str, row_number: int, value: str, style: str | None = None) -> None:
    cell = ET.SubElement(row, f"{{{silver.NS}}}c", {"r": f"{col}{row_number}", "t": "inlineStr"})
    if style is not None:
        cell.set("s", style)
    inline = ET.SubElement(cell, f"{{{silver.NS}}}is")
    text = ET.SubElement(inline, f"{{{silver.NS}}}t")
    text.text = value


def write_final_workbook(rows: list[dict[str, str]], results: dict[str, dict[int, list[dict[str, str]]]], reviewed: dict[int, dict[str, str]]) -> None:
    model_headers: list[str] = []
    for model in MODELS:
        for rank in range(1, 4):
            model_headers += [f"{model}_category_{rank}", f"{model}_subcategory_{rank}", f"{model}_justification_{rank}", f"{model}_confidence_{rank}"]
    headers = model_headers + ["review_category", "review_subcategory", "review_justification", "review_basis", "reviewed_by_ai"]
    with ZipFile(INPUT) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(files["xl/worksheets/sheet1.xml"])
    sheet_data = root.find(f"{{{silver.NS}}}sheetData")
    if sheet_data is None:
        raise ValueError("input workbook has no sheet data")
    first_extra = 4
    extra_cols = [excel_col(first_extra + i) for i in range(len(headers))]
    for row_el in sheet_data.findall(f"{{{silver.NS}}}row"):
        row_num = int(row_el.get("r", "0"))
        if row_num == 1:
            for col, header in zip(extra_cols, headers):
                set_cell(row_el, col, row_num, header, "1")
        elif row_num >= 2:
            values: list[str] = []
            for model in MODELS:
                matches = results[model][row_num]
                for rank in range(3):
                    match = matches[rank] if rank < len(matches) else {}
                    values += [match.get("category", ""), match.get("subcategory", ""), match.get("justification", ""), match.get("confidence", "")]
            review = reviewed[row_num]
            values += [review["category"], review["subcategory"], review["justification"], choose_review(row_num, results)[1], "yes"]
            for col, value in zip(extra_cols, values):
                set_cell(row_el, col, row_num, value, "2")
            for existing in row_el.findall(f"{{{silver.NS}}}c"):
                if existing.get("r", "").startswith(("A", "B", "C")):
                    existing.set("s", "2")
    dimension = root.find(f"{{{silver.NS}}}dimension")
    if dimension is not None:
        dimension.set("ref", f"A1:{extra_cols[-1]}{len(rows)}")
    cols = root.find(f"{{{silver.NS}}}cols")
    if cols is None:
        cols = ET.Element(f"{{{silver.NS}}}cols")
        root.insert(2, cols)
    for i in range(len(headers)):
        width = 70 if "justification" in headers[i] else 30
        ET.SubElement(cols, f"{{{silver.NS}}}col", {"width": str(width), "customWidth": "1", "min": str(first_extra + i), "max": str(first_extra + i)})
    auto_filter = root.find(f"{{{silver.NS}}}autoFilter")
    if auto_filter is None:
        auto_filter = ET.SubElement(root, f"{{{silver.NS}}}autoFilter")
    auto_filter.set("ref", f"A1:{extra_cols[-1]}{len(rows)}")
    files["xl/worksheets/sheet1.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=False)
    files["xl/styles.xml"] = silver.update_styles(files["xl/styles.xml"])
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        for name, data in files.items():
            archive.writestr(name, data)


def main() -> int:
    rows, results = load_results()
    taxonomy, valid_pairs = silver.read_taxonomy(TAXONOMY)
    reviewed = write_review_json(rows, results)
    for row_id, item in reviewed.items():
        if (item["category"], item["subcategory"]) not in valid_pairs:
            raise ValueError(f"review choice for row {row_id} is not in detailed taxonomy")
    write_final_workbook(rows, results, reviewed)
    print(f"wrote {OUTPUT} and {REVIEW_DIR / 'final_review.json'}")
    print(f"manual reviews: {len(MANUAL)}; rows: {len(reviewed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
