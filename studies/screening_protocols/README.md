# Hardcoded Question Panels (Deterministic Screening Protocols)

This directory contains the **6 hardcoded question panels** (deterministic screening protocols) used by the FETCH legal intake and classification pipeline.

Unlike LLM-generated follow-up questions—which dynamically probe missing details—these 6 panels are **invariant, rule-based screening instruments**. They serve safety-critical intake functions where non-deterministic AI outputs are unacceptable (e.g., immediate domestic violence threats, elder financial exploitation, deportation risk, police misconduct, whistleblower retaliation, and third-party workplace injuries).

---

## Key Design Principles

1. **Safety-Critical & Hallucination-Free:** Question text and choice options are deterministic data, never rewritten by LLMs.
2. **Bilingual Support (EN / ES):** Every question and choice option includes canonical English and Spanish translations.
3. **Mandatory Taxonomy Override:** Specific affirmative choices force mandatory legal taxonomy categories (e.g., `family.restraining_orders`, `wills_trusts.elder_abuse`) regardless of model confidence scores.
4. **Emergency Safety Triggers:** Choices trigger specific informational/warning flags (`domestic_violence_immediate_danger`, `vulnerable_adult_immediate_assistance`, `police_misconduct_time_sensitive`).
5. **Narrative Fact Suppression:** Regular expression pattern matching scans opening narrative text to suppress questions or choice options when facts are already disclosed or ruled out.

---

## Overview of the 6 Question Panels

| # | Protocol ID | Priority | Subject Area | Mandatory Taxonomy Category | Risk Levels |
|---|---|---|---|---|---|
| 1 | `family_safety.v1` | 100 | Family Safety & Restraining Orders | `Family Law > Restraining Orders` | `none`, `informational`, `elevated`, `urgent` |
| 2 | `elder_exploitation.v1` | 90 | Elder Abuse & Financial Exploitation | `Wills & Trusts > Elder Abuse` | `none`, `informational`, `elevated`, `urgent` |
| 3 | `immigration_consequences.v1` | 80 | Immigration Status & Deportation Risk | `International Law > General Immigration/Visas`, `International Law > Deportation` | `none`, `informational`, `elevated` |
| 4 | `police_government_claim.v1` | 70 | Actions Against Police & Tort Claims | `General Litigation > Actions Against Police`, `General Litigation > Tort Claims Act` | `none`, `informational`, `elevated` |
| 5 | `employment_retaliation.v1` | 60 | Whistleblower & Retaliation | `Labor & Employment > Whistleblowers - Employee`, `Labor & Employment > Wrongful Discharge - Employee` | `none`, `informational`, `elevated` |
| 6 | `work_injury_third_party.v1` | 50 | Workplace Injury Third-Party Claims | `Workers' Comp > Third Party Litigation` | `none`, `informational` |

---

## Detailed Specifications

### 1. Family Safety Protocol (`family_safety.v1`)
* **Trigger Terms / Patterns:** Divorce, separation, child custody, visitation, parenting time, paternity, restraining order, spouse, partner, ex.
* **Question (EN):** *"Has anyone involved in this family or relationship situation done any of the following?"*
* **Question (ES):** *"¿Alguna persona involucrada en esta situación familiar o de pareja ha hecho algo de lo siguiente?"*
* **Format:** Checkbox (Multiple choice)
* **Choices & Outcomes:**
  * `none`: *"No, none of these"* → Risk: `none`
  * `controlling_or_threatening`: *"Controlled, monitored, stalked, threatened, or repeatedly harassed me or someone else"* → Risk: `informational` \| Trigger: `domestic_violence_safety_resources` \| Route: `family.restraining_orders`
  * `physical_or_sexual_harm`: *"Physically hurt, sexually harmed, strangled, or threatened someone with a weapon"* → Risk: `elevated` \| Trigger: `domestic_violence_elevated_risk` \| Route: `family.restraining_orders`
  * `immediate_danger`: *"Someone may be in immediate danger now"* → Risk: `urgent` \| Trigger: `domestic_violence_immediate_danger` \| Route: `family.restraining_orders`
  * `not_sure`: *"I am not sure"* → Risk: `informational` \| Trigger: `domestic_violence_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

### 2. Elder Exploitation Protocol (`elder_exploitation.v1`)
* **Trigger Terms / Patterns:** Wills & trusts, elder abuse, guardianship, conservatorship, probate, older adult, vulnerable adult, power of attorney, caregiver.
* **Question (EN):** *"Has anyone involved in the older or vulnerable adult’s care or finances done any of the following?"*
* **Question (ES):** *"¿Alguna persona involucrada en el cuidado o las finanzas del adulto mayor o vulnerable ha hecho algo de lo siguiente?"*
* **Format:** Checkbox (Multiple choice)
* **Choices & Outcomes:**
  * `none`: *"No, none of these"* → Risk: `none`
  * `pressure_or_control`: *"Pressured or controlled decisions about money, property, accounts, a will, trust, or power of attorney"* → Risk: `informational` \| Trigger: `elder_exploitation_resources` \| Route: `wills_trusts.elder_abuse`
  * `taking_assets`: *"Took, transferred, hid, or used money or property without permission"* → Risk: `elevated` \| Trigger: `elder_exploitation_elevated` \| Route: `wills_trusts.elder_abuse`
  * `basic_needs_or_safety`: *"Left the person without access to money, housing, medication, care, or other basic needs"* → Risk: `urgent` \| Trigger: `vulnerable_adult_immediate_assistance` \| Route: `wills_trusts.elder_abuse`
  * `not_sure`: *"I am not sure"* → Risk: `informational` \| Trigger: `elder_exploitation_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

### 3. Immigration Consequences Protocol (`immigration_consequences.v1`)
* **Trigger Terms / Patterns:** International Law > Deportation / General Immigration, visa, green card, citizenship, ICE, immigration court, removal proceedings.
* **Question (EN):** *"Could this situation affect anyone’s ability to stay in the United States, renew immigration status, obtain a visa or green card, become a citizen, or avoid deportation?"*
* **Question (ES):** *"¿Podría esta situación afectar la capacidad de alguien para permanecer en Estados Unidos, renovar su estatus migratorio, obtener una visa o tarjeta de residencia, hacerse ciudadano/a o evitar la deportación?"*
* **Format:** Radio (Single select)
* **Choices & Outcomes:**
  * `no`: *"No"* → Risk: `none`
  * `application_or_status`: *"Yes, it may affect an application, visa, green card, citizenship, or current status"* → Risk: `informational` \| Trigger: `immigration_status_consequences` \| Route: `international.general_immigration_visas`
  * `removal_or_deportation`: *"Yes, someone has received an ICE, immigration-court, removal, or deportation notice"* → Risk: `elevated` \| Trigger: `immigration_removal_time_sensitive` \| Route: `international.deportation`
  * `not_sure`: *"I am not sure"* → Risk: `informational` \| Trigger: `immigration_consequences_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

### 4. Police & Government Claims Protocol (`police_government_claim.v1`)
* **Trigger Terms / Patterns:** Actions against police, tort claims act, police officer, arrest, detention, search, excessive force, false arrest, government agency/employee.
* **Question (EN):** *"Which best describes the help you may need after the police or government encounter?"*
* **Question (ES):** *"¿Qué opción describe mejor la ayuda que podría necesitar después del encuentro con la policía o el gobierno?"*
* **Format:** Radio (Single select)
* **Choices & Outcomes:**
  * `criminal_defense_only`: *"Help defending against a charge, citation, probation issue, or criminal case"* → Risk: `none`
  * `police_misconduct`: *"Help concerning excessive force, false arrest, an unlawful search, malicious prosecution, or other police misconduct"* → Risk: `elevated` \| Trigger: `police_misconduct_time_sensitive` \| Route: `general_litigation.actions_against_police`
  * `government_injury_or_loss`: *"Help for an injury or loss caused by a government agency or government employee"* → Risk: `elevated` \| Trigger: `government_claim_time_sensitive` \| Route: `general_litigation.tort_claims_act`
  * `both_criminal_and_misconduct`: *"Both defending a criminal case and addressing possible police misconduct"* → Risk: `elevated` \| Trigger: `police_misconduct_and_criminal_case` \| Route: `general_litigation.actions_against_police`
  * `not_sure`: *"I am not sure"* → Risk: `informational` \| Trigger: `police_encounter_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

### 5. Employment Retaliation Protocol (`employment_retaliation.v1`)
* **Trigger Terms / Patterns:** Labor & Employment, whistleblower, wrongful discharge, fired, terminated, demoted, reduced hours, forced resignation, reported illegal/unsafe conduct.
* **Question (EN):** *"Did your employer fire, discipline, threaten, reduce your hours, or otherwise act against you after you reported illegal, unsafe, fraudulent, or dishonest conduct?"*
* **Question (ES):** *"¿Su empleador lo/la despidió, disciplinó, amenazó, redujo sus horas o tomó otras represalias después de que usted denunció una conducta ilegal, insegura, fraudulenta o deshonesta?"*
* **Format:** Radio (Single select)
* **Choices & Outcomes:**
  * `no`: *"No"* → Risk: `none`
  * `yes_not_fired`: *"Yes, but I was not fired or forced to quit"* → Risk: `elevated` \| Trigger: `employment_retaliation_time_sensitive` \| Route: `employment.whistleblowers`
  * `yes_fired`: *"Yes, and I was fired or forced to quit"* → Risk: `elevated` \| Trigger: `employment_retaliation_time_sensitive` \| Routes: `employment.whistleblowers`, `employment.wrongful_discharge`
  * `not_sure`: *"I am not sure whether the employer’s action was connected to my report"* → Risk: `informational` \| Trigger: `employment_retaliation_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

### 6. Workplace Injury Third-Party Claims Protocol (`work_injury_third_party.v1`)
* **Trigger Terms / Patterns:** Workers' comp, work injury, occupational accident, injury on job, hit/injured by driver, contractor, property owner, manufacturer.
* **Question (EN):** *"Was your work injury caused by someone other than your employer or a coworker—for example, a driver, contractor, property owner, or product manufacturer?"*
* **Question (ES):** *"¿Su lesión laboral fue causada por alguien que no fuera su empleador o un compañero de trabajo, por ejemplo, un conductor, contratista, propietario o fabricante de un producto?"*
* **Format:** Radio (Single select)
* **Choices & Outcomes:**
  * `no`: *"No"* → Risk: `none`
  * `yes`: *"Yes"* → Risk: `informational` \| Trigger: `work_injury_possible_third_party_claim` \| Route: `workers_comp.third_party_litigation`
  * `not_sure`: *"I am not sure"* → Risk: `informational` \| Trigger: `work_injury_third_party_general_information`
  * `prefer_not`: *"I prefer not to answer"* → Risk: `none`

---

## Directory Contents

* [`screening_protocols.py`](file:///home/quinten/fetch/publishable-repo/question_panels/screening_protocols.py): Python implementation containing protocol data structures, pattern matchers, choice suppression, and mandatory routing logic.
* [`question_panels.json`](file:///home/quinten/fetch/publishable-repo/question_panels/question_panels.json): Complete pre-rendered JSON export of all 6 panels for non-Python frontends or schema validation.
* [`test_screening_protocols.py`](file:///home/quinten/fetch/publishable-repo/question_panels/test_screening_protocols.py): Pytest unit test suite verifying all 46 protocol assertions.

---

## Running the Unit Tests

```bash
PYTHONPATH=. pytest question_panels/test_screening_protocols.py
```
