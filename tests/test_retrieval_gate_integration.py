import unittest
from unittest.mock import patch

from src.graph_routing import get_query_status, route_after_retrieval
from src.knowledge_node import retrieve_knowledge_node


class TestRetrievalGateIntegration(unittest.TestCase):
    def _state(self, question):
        return {
            "user_question": question,
            "schema_context": "",
            "cache_hit": False,
            "retrieval_relevant": False,
            "retrieval_score": 0.0,
            "retrieval_error": "",
        }

    def _retrieval_result(self, score):
        return [{
            "query_max_semantic_score": score,
            "type": "schema",
            "source": "schema_customers",
            "score": score,
            "text": "customers(customer_id, customer_name, signup_date)",
        }]

    @patch("src.knowledge_node.get_min_semantic_score", return_value=0.302452)
    @patch("src.knowledge_node.retrieve_knowledge")
    def test_business_question_passes_gate(self, retrieve, _threshold):
        retrieve.return_value = self._retrieval_result(0.519107)
        result = retrieve_knowledge_node(self._state("Which customers signed up recently?"))
        self.assertTrue(result["retrieval_relevant"])
        self.assertEqual(result["retrieval_error"], "")
        self.assertIn("schema_customers", result["schema_context"])

    @patch("src.knowledge_node.get_min_semantic_score", return_value=0.302452)
    @patch("src.knowledge_node.retrieve_knowledge")
    def test_weather_question_is_rejected(self, retrieve, _threshold):
        retrieve.return_value = self._retrieval_result(0.062852)
        result = retrieve_knowledge_node(self._state("What is the weather tomorrow?"))
        self.assertFalse(result["retrieval_relevant"])
        self.assertEqual(result["schema_context"], "")
        self.assertTrue(result["retrieval_error"])

    @patch("src.knowledge_node.get_min_semantic_score", return_value=0.302452)
    @patch("src.knowledge_node.retrieve_knowledge")
    def test_programming_question_is_rejected(self, retrieve, _threshold):
        retrieve.return_value = self._retrieval_result(0.044449)
        result = retrieve_knowledge_node(self._state("Explain Python decorators."))
        self.assertFalse(result["retrieval_relevant"])

    @patch("src.knowledge_node.get_min_semantic_score", return_value=0.302452)
    @patch("src.knowledge_node.retrieve_knowledge")
    def test_payroll_question_is_rejected(self, retrieve, _threshold):
        retrieve.return_value = self._retrieval_result(0.287288)
        result = retrieve_knowledge_node(self._state("Calculate employee payroll."))
        self.assertFalse(result["retrieval_relevant"])

    def test_irrelevant_cached_question_is_rejected_before_cache_validation(self):
        self.assertEqual(
            route_after_retrieval({
                "retrieval_relevant": False,
                "cache_hit": True,
            }),
            "reject",
        )

    def test_relevant_cache_hit_uses_cached_sql_path(self):
        self.assertEqual(
            route_after_retrieval({
                "retrieval_relevant": True,
                "cache_hit": True,
            }),
            "cached",
        )

    def test_relevant_cache_miss_uses_generation_path(self):
        self.assertEqual(
            route_after_retrieval({
                "retrieval_relevant": True,
                "cache_hit": False,
            }),
            "generate",
        )

    def test_api_status_distinguishes_rejection(self):
        self.assertEqual(
            get_query_status({"retrieval_relevant": False}),
            "rejected",
        )

    def test_api_status_distinguishes_success_and_error(self):
        self.assertEqual(
            get_query_status({"retrieval_relevant": True}),
            "completed",
        )
        self.assertEqual(
            get_query_status({
                "retrieval_relevant": True,
                "execution_error": "database unavailable",
            }),
            "error",
        )

    def test_api_status_reports_pending_approval(self):
        self.assertEqual(
            get_query_status({
                "retrieval_relevant": True,
                "approval_required": True,
            }),
            "awaiting_approval",
        )


if __name__ == "__main__":
    unittest.main()
