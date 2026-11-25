import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.api import app


class TestQueryApiEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _retrieval_documents(self, score):
        return [{
            "query_max_semantic_score": score,
            "type": "schema",
            "source": "schema_orders",
            "score": score,
            "text": "orders(order_id, customer_id, order_date, status); order_items(order_id, product_id, quantity); products(product_id, product_name, category, price)",
        }]

    def _mock_completion(self, sql):
        return SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=sql)
            )]
        )

    @patch("src.cache_store_node.cache_sql")
    @patch("src.evaluator.evaluate_sql", return_value=(True, ""))
    @patch("src.nodes._generate_with_rate_limit_retry")
    @patch("src.knowledge_node.retrieve_knowledge")
    @patch("src.cache_node.get_cached_sql", return_value=None)
    def test_revenue_query_runs_through_real_graph_with_mocked_llm(
        self, _cache, retrieve, generate, _judge, _store
    ):
        sql = (
            "SELECT p.category, "
            "SUM(oi.quantity * p.price) AS revenue "
            "FROM order_items AS oi "
            "JOIN products AS p ON oi.product_id = p.product_id "
            "GROUP BY p.category ORDER BY revenue DESC"
        )
        retrieve.return_value = self._retrieval_documents(0.438493)
        generate.return_value = self._mock_completion(sql)

        response = self.client.post(
            "/query",
            json={"question": "Show total revenue by product category.", "role": "analyst"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertEqual(body["sql"], sql)
        self.assertTrue(body["result"])
        generate.assert_called_once()

    @patch("src.knowledge_node.retrieve_knowledge")
    @patch("src.cache_node.get_cached_sql", return_value=None)
    def test_three_out_of_domain_questions_are_rejected_without_generation(
        self, _cache, retrieve
    ):
        cases = [
            ("What is the weather tomorrow?", 0.062852),
            ("Explain Python decorators.", 0.044449),
            ("Calculate employee payroll.", 0.287288),
        ]
        for question, score in cases:
            with self.subTest(question=question):
                retrieve.return_value = self._retrieval_documents(score)
                with patch("src.nodes._generate_with_rate_limit_retry") as generate:
                    response = self.client.post(
                        "/query",
                        json={"question": question, "role": "analyst"},
                    )
                self.assertEqual(response.status_code, 200, response.text)
                body = response.json()
                self.assertEqual(body["status"], "rejected")
                self.assertEqual(body["sql"], "")
                self.assertEqual(body["result"], [])
                self.assertTrue(body["error"])
                generate.assert_not_called()

    @patch("src.knowledge_node.retrieve_knowledge")
    @patch("src.cache_node.get_cached_sql")
    def test_irrelevant_question_with_cache_hit_is_rejected_and_cached_sql_is_cleared(
        self, cached_sql, retrieve
    ):
        cached_sql.return_value = "SELECT 123 AS cached_value"
        retrieve.return_value = self._retrieval_documents(0.062852)
        with patch("src.nodes._generate_with_rate_limit_retry") as generate:
            response = self.client.post(
                "/query",
                json={"question": "What is the weather tomorrow?", "role": "analyst"},
            )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "rejected")
        self.assertEqual(body["sql"], "")
        self.assertTrue(body["cache_hit"])
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
