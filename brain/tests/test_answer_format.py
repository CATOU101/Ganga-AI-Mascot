from brain.answer_format import detect_answer_format, strip_answer_formatting_instructions
from brain.token_budgets import TokenBudgets
from brain.config import BrainConfig
from brain.retriever import Retriever


def test_format_detection_respects_user_requested_structure_and_detail():
    comparison = detect_answer_format("Compare the Ganga and Yamuna in a table")
    assert comparison.style == "comparison_table"
    assert detect_answer_format("Give five reasons with examples").points == 5
    assert detect_answer_format("List steps to protect rivers").style == "steps"
    assert detect_answer_format("Explain briefly").detail == "brief"
    assert detect_answer_format("Explain in detail").detail == "detailed"
    assert detect_answer_format("Write about 120 words").word_count == 120
    assert detect_answer_format("Explain in paragraphs").style == "paragraphs"
    assert detect_answer_format("Tell me about the Ganga in points.").style == "bullets"
    five_points = detect_answer_format("Explain the importance of the Ganga in five points.")
    assert five_points.style == "numbered"
    assert five_points.points == 5
    assert strip_answer_formatting_instructions("Tell me about the Ganga in points.") == "Tell me about the Ganga."
    assert strip_answer_formatting_instructions("Explain the importance of the Ganga in five points.") == "Explain the importance of the Ganga."
    assert strip_answer_formatting_instructions("Tell me about Ganga pollution.") == "Tell me about Ganga pollution."


def test_token_budget_scales_by_request_and_stays_bounded():
    budgets = TokenBudgets()
    assert budgets.output_for(detect_answer_format("What is a river?"), general=True) == budgets.general_short
    assert budgets.output_for(detect_answer_format("Compare two rivers")) == budgets.comparison
    assert budgets.output_for(detect_answer_format("Explain in detail")) == budgets.detailed
    assert budgets.output_for(detect_answer_format("Write about 2000 words")) <= budgets.complex


def test_retrieval_drops_duplicate_chunks_while_preserving_distinct_evidence():
    config = BrainConfig(llm_provider="extractive")
    retriever = Retriever(config, store=object())
    first = {
        "chunk_id": "one", "text": "The Ganga river flows through the basin.",
        "metadata": {"file_name": "report.pdf", "page_start": 2, "title": "Ganga"},
        "distance": 0.1,
    }
    duplicate = {**first, "chunk_id": "duplicate"}
    distinct = {
        "chunk_id": "two", "text": "The Ganga river supports communities across the basin.",
        "metadata": {"file_name": "report.pdf", "page_start": 3, "title": "Ganga"},
        "distance": 0.2,
    }
    sufficient, hits = retriever.rerank_and_filter("Ganga river", [first, duplicate, distinct], top_k=3)
    assert sufficient is True
    assert [hit["chunk_id"] for hit in hits] == ["one", "two"]
