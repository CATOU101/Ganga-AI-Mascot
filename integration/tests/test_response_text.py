from integration.avatar.response_text import spoken_response
from integration.models.brain_response import AvatarPresentation, BrainResponse, CitationItem
from integration.avatar.mascot_presenter import MascotPresenter


def test_spoken_response_removes_markdown_but_keeps_answer_content():
    assert spoken_response("## Findings\n- **DO:** 6 mg/L.\n- See [CPCB](https://example.test).") == (
        "Findings DO: 6 mg/L. See CPCB."
    )


def test_presenter_keeps_display_answer_and_sets_plain_spoken_text():
    answer = "**Aviral Dhara** supports continuous flow."
    response = BrainResponse(
        answer=answer,
        input_language="en",
        output_language="en",
        language="en",
        citations=[CitationItem(source="GRBMP")],
    )

    presentation = MascotPresenter().create_presentation(response)

    assert presentation.answer == answer
    assert presentation.spoken_text == "Aviral Dhara supports continuous flow."
    assert presentation.citations[0].source == "GRBMP"


def test_presentation_without_spoken_text_remains_backward_compatible():
    presentation = AvatarPresentation(answer="The reading is stale.")

    assert presentation.spoken_text == ""
    assert spoken_response(presentation.spoken_text or presentation.answer) == "The reading is stale."
