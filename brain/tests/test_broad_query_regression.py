"""Regression tests for broad query retrieval, keyword extraction, and metadata cleaning."""

import unittest

from brain.config import load_config
from brain.embeddings import get_embedding_function
from brain.generator import build_generator, clean_hit_text
from brain.rag_pipeline import answer_question
from brain.retriever import (
    Retriever,
    extract_keywords,
    is_broad_ganga_query,
    asks_for_current_information,
)
from brain.vector_store import get_chroma_vector_store


class TestBroadQueryRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_config()
        cls.embedding = get_embedding_function(
            cls.config.embedding_provider,
            cls.config.embedding_dimensions,
            cls.config.ort_threads,
        )
        cls.store = get_chroma_vector_store(cls.config)
        cls.retriever = Retriever(cls.config, cls.store)
        cls.generator = build_generator(cls.config.llm_provider, cls.config.llm_model)

    def test_keywords_extraction_includes_domain_terms(self):
        """Verify 'ganga' and 'river' are no longer treated as stopwords."""
        kws = extract_keywords("tell me about Ganga")
        self.assertIn("ganga", kws)
        self.assertNotIn("tell", kws)
        self.assertNotIn("about", kws)

    def test_broad_query_detection_heuristic(self):
        """Verify is_broad_ganga_query correctly distinguishes broad vs specific queries."""
        self.assertTrue(is_broad_ganga_query("tell me about Ganga"))
        self.assertTrue(is_broad_ganga_query("Tell me about the Ganga"))
        self.assertTrue(is_broad_ganga_query("What is Ganga?"))
        self.assertTrue(is_broad_ganga_query("Overview of Ganga River"))

        self.assertFalse(is_broad_ganga_query("What is Aviral Dhara?"))
        self.assertFalse(is_broad_ganga_query("What is NGRBA?"))
        self.assertFalse(is_broad_ganga_query("What is the population of Mars?"))
        self.assertFalse(is_broad_ganga_query("What is the current water quality of the Ganga today?"))

    def test_broad_query_tell_me_about_ganga(self):
        """Test A: Broad query 'tell me about Ganga' produces broad overview."""
        res = answer_question("tell me about Ganga")
        self.assertEqual(res["mode"], "grounded")
        ans = res["answer"].lower()
        self.assertNotIn("ngrba", ans)
        self.assertNotIn("report code:", ans)
        self.assertNotIn("p a g e", ans)
        # Check citations come from overview evidence
        citations_str = " ".join([c["source"].lower() for c in res["citations"]])
        self.assertTrue(
            "at a glance" in citations_str or "main plan" in citations_str or "summary" in citations_str or "interim" in citations_str,
            f"Unexpected citations: {citations_str}"
        )

    def test_broad_query_tell_me_about_the_ganga(self):
        """Test B: Broad query 'Tell me about the Ganga' produces grounded answer."""
        res = answer_question("Tell me about the Ganga")
        self.assertEqual(res["mode"], "grounded")
        self.assertNotIn("report code:", res["answer"].lower())

    def test_broad_query_what_is_ganga(self):
        """Test C: Broad query 'What is Ganga?' produces grounded overview."""
        res = answer_question("What is Ganga?")
        self.assertEqual(res["mode"], "grounded")
        self.assertNotIn("report code:", res["answer"].lower())

    def test_broad_query_overview_of_ganga_river(self):
        """Test D: Broad query 'Overview of Ganga River' produces grounded overview."""
        res = answer_question("Overview of Ganga River")
        self.assertEqual(res["mode"], "grounded")
        self.assertNotIn("report code:", res["answer"].lower())

    def test_specific_query_aviral_dhara(self):
        """Test E: Specific query 'What is Aviral Dhara?' retains Mission 1 / Aviral Dhara focus."""
        res = answer_question("What is Aviral Dhara?")
        self.assertEqual(res["mode"], "grounded")
        ans = res["answer"].lower()
        self.assertIn("aviral dhara", ans)

    def test_specific_query_ngrba(self):
        """Test F: Specific query 'What is NGRBA?' retains institutional / NGRBA focus."""
        res = answer_question("What is NGRBA?")
        self.assertEqual(res["mode"], "grounded")

    def test_unsupported_query_mars(self):
        """Test G: Unsupported query 'What is the population of Mars?' triggers insufficient evidence fallback."""
        res = answer_question("What is the population of Mars?")
        self.assertEqual(res["mode"], "insufficient-evidence")

    def test_current_info_query_water_quality(self):
        """Test H: Current info query triggers current-info fallback."""
        res = answer_question("What is the current water quality of the Ganga today?")
        self.assertEqual(res["mode"], "current-info-fallback")

    def test_sentence_cleaner_removes_report_metadata(self):
        """Test I: clean_hit_text strips report codes and page artifacts."""
        sample = (
            "[Page 90]\n"
            "Report Code: 011_GBP_IIT_PLG_DAT_01_Ver 1_Dec 2011\n"
            "90 | P a g e\n"
            "GRBMP – January 2015: Mission 1 – Aviral Dhara\n"
            "The Ganga originates from Gaumukh."
        )
        cleaned = clean_hit_text(sample)
        self.assertNotIn("[Page 90]", cleaned)
        self.assertNotIn("Report Code:", cleaned)
        self.assertNotIn("P a g e", cleaned)
        self.assertIn("The Ganga originates from Gaumukh.", cleaned)


if __name__ == "__main__":
    unittest.main()
