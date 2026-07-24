import pytest
from question_panels.screening_protocols import (
    CATEGORY_LABELS,
    PROTOCOLS,
    EffectiveCategory,
    Label,
    MandatoryCategory,
    ScreeningAnswer,
    build_effective_categories,
    build_mandatory_categories,
    evaluate_answers,
    resolve_narrative,
    select_questions,
)


def _answer(protocol, choice_id):
    return ScreeningAnswer(
        protocol_id=protocol.protocol_id,
        question_id=protocol.question_id,
        choice_id=choice_id,
    )


@pytest.mark.parametrize(
    "protocol,choice",
    [(protocol, choice) for protocol in PROTOCOLS for choice in protocol.choices],
)
def test_every_choice_produces_exact_configured_outcome(protocol, choice):
    result = evaluate_answers([_answer(protocol, choice.id)])[0]

    assert result.protocol_id == protocol.protocol_id
    assert result.protocol_version == protocol.version
    assert result.question_id == protocol.question_id
    assert result.choice_id == choice.id
    assert result.risk_level == choice.outcome.risk_level
    assert result.information_trigger == choice.outcome.information_trigger
    assert result.mandatory_category_ids == list(choice.outcome.mandatory_category_ids)


def test_none_and_prefer_not_never_create_mandatory_categories():
    for protocol in PROTOCOLS:
        for choice in protocol.choices:
            if choice.id in {"none", "no", "prefer_not", "criminal_defense_only"}:
                result = evaluate_answers([_answer(protocol, choice.id)])[0]
                assert not result.mandatory_category_ids


def test_only_explicit_urgent_choices_are_urgent():
    for protocol in PROTOCOLS:
        for choice in protocol.choices:
            result = evaluate_answers([_answer(protocol, choice.id)])[0]
            assert (result.risk_level == "urgent") == (
                choice.id in {"immediate_danger", "basic_needs_or_safety"}
            )


def test_checkbox_answer_can_return_multiple_deterministic_outcomes():
    family = PROTOCOLS[0]
    answer = ScreeningAnswer(
        protocol_id=family.protocol_id,
        question_id=family.question_id,
        choice_ids=["controlling_or_threatening", "physical_or_sexual_harm"],
    )

    results = evaluate_answers([answer])

    assert [result.choice_id for result in results] == [
        "controlling_or_threatening",
        "physical_or_sexual_harm",
    ]
    assert [result.risk_level for result in results] == [
        "informational",
        "elevated",
    ]


def test_checkbox_answer_rejects_exclusive_choice_combination():
    family = PROTOCOLS[0]
    answer = ScreeningAnswer(
        protocol_id=family.protocol_id,
        question_id=family.question_id,
        choice_ids=["none", "physical_or_sexual_harm"],
    )

    with pytest.raises(ValueError, match="Exclusive choice"):
        evaluate_answers([answer])


def test_effective_categories_preserve_confidence_and_protocol_only_null():
    family = PROTOCOLS[0]
    result = evaluate_answers([_answer(family, "physical_or_sexual_harm")])
    mandatory = build_mandatory_categories(result)
    labels = [
        Label(label=CATEGORY_LABELS["family.restraining_orders"], confidence=1.8),
        Label(label="Family Law > Divorce/Separation", confidence=2.4),
    ]

    effective = build_effective_categories(labels, mandatory)

    assert len(effective) == 2
    restraining = effective[0]
    assert restraining.confidence == 1.8
    assert restraining.mandatory is True
    assert restraining.sources == ["model", "protocol"]
    assert effective[1].label == "Family Law > Divorce/Separation"

    protocol_only = build_effective_categories([], mandatory)[0]
    assert protocol_only.confidence is None
    assert protocol_only.mandatory is True
    assert protocol_only.sources == ["protocol"]


def test_mandatory_routes_are_not_subject_to_three_label_limit():
    employment = next(
        protocol
        for protocol in PROTOCOLS
        if protocol.protocol_id == "employment_retaliation.v1"
    )
    results = evaluate_answers([_answer(employment, "yes_fired")])
    mandatory = build_mandatory_categories(results)
    labels = [
        Label(label=f"Unrelated > Category {number}", confidence=3 - number / 10)
        for number in range(3)
    ]

    effective = build_effective_categories(labels, mandatory)

    assert len(effective) == 5
    assert {category.id for category in effective if category.mandatory} == {
        "employment.whistleblowers",
        "employment.wrongful_discharge",
    }
    assert all(category.confidence is None for category in effective[3:])


def test_questions_are_bilingual_and_expose_translation_invariants():
    english = select_questions("I am getting divorced.", [], [], "en")
    spanish = select_questions("Me estoy divorciando.", [], [], "es")

    assert english[0].protocol_id == spanish[0].protocol_id == "family_safety.v1"
    assert english[0].format == spanish[0].format == "checkbox"
    assert english[0].question_id == spanish[0].question_id
    assert english[0].translation_key == spanish[0].translation_key
    assert english[0].question == english[0].translations.en
    assert spanish[0].question == spanish[0].translations.es
    assert [choice.id for choice in english[0].choices] == [
        choice.id for choice in spanish[0].choices
    ]
    assert all(
        choice.resolution_status == "unresolved" for choice in english[0].choices
    )


def test_priority_caps_protocol_questions_and_completed_protocol_is_suppressed():
    labels = [
        "Family Law > Divorce/Separation",
        "Wills & Trusts > Elder Abuse",
        "International Law > Deportation",
        "General Litigation > Actions Against Police",
        "Labor & Employment > Wrongful Discharge - Employee",
        "Workers' Comp > Third Party Litigation",
    ]

    questions = select_questions("", labels, [], limit=3)
    assert [question.protocol_id for question in questions] == [
        "family_safety.v1",
        "elder_exploitation.v1",
        "immigration_consequences.v1",
    ]

    completed = select_questions(
        "I am getting divorced.", labels[:1], ["family_safety.v1"]
    )
    assert completed == []


@pytest.mark.parametrize(
    "text,labels,protocol_id,disclosed_choice_id,question_remains",
    [
        (
            "I am divorcing my husband because he strangled me.",
            [],
            "family_safety.v1",
            "physical_or_sexual_harm",
            True,
        ),
        (
            "The caregiver stole my elderly mother's money.",
            [],
            "elder_exploitation.v1",
            "taking_assets",
            True,
        ),
        (
            "I received an ICE deportation notice.",
            [],
            "immigration_consequences.v1",
            "removal_or_deportation",
            True,
        ),
        (
            "The police used excessive force during my arrest.",
            [],
            "police_government_claim.v1",
            "police_misconduct",
            True,
        ),
        (
            "My employer fired me after I reported fraud.",
            [],
            "employment_retaliation.v1",
            "yes_fired",
            False,
        ),
        (
            "A driver hit me while I was driving for work.",
            [],
            "work_injury_third_party.v1",
            "yes",
            False,
        ),
    ],
)
def test_explicit_narrative_answer_suppresses_disclosed_choice(
    text, labels, protocol_id, disclosed_choice_id, question_remains
):
    questions = {
        question.protocol_id: question
        for question in select_questions(text, labels, [])
    }
    assert (protocol_id in questions) is question_remains
    if question_remains:
        assert disclosed_choice_id not in {
            choice.id for choice in questions[protocol_id].choices
        }

    resolutions = resolve_narrative(text, labels)
    assert any(
        resolution.protocol_id == protocol_id
        and resolution.choice_id == disclosed_choice_id
        and resolution.status == "disclosed"
        for resolution in resolutions
    )
