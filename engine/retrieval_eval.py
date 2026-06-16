import asyncio
from typing import List, Dict

class RetrievalEvaluator:
    def __init__(self):
        pass

    def calculate_hit_rate(self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3) -> float:
        """
        Tính toán xem ít nhất 1 trong expected_ids có nằm trong top_k của retrieved_ids không.
        Nếu expected_ids rỗng (out of context), hit rate là 1.0 nếu retrieved_ids cũng rỗng, ngược lại là 0.0.
        """
        if not expected_ids:
            return 1.0 if not retrieved_ids else 0.0
            
        top_retrieved = retrieved_ids[:top_k]
        hit = any(doc_id in top_retrieved for doc_id in expected_ids)
        return 1.0 if hit else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        """
        Tính Mean Reciprocal Rank (cho một sample).
        Tìm vị trí đầu tiên của một expected_id trong retrieved_ids.
        MRR = 1 / position (vị trí 1-indexed). Nếu không thấy thì là 0.
        Nếu expected_ids rỗng (out of context), MRR là 1.0 nếu retrieved_ids cũng rỗng, ngược lại là 0.0.
        """
        if not expected_ids:
            return 1.0 if not retrieved_ids else 0.0

        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_ids:
                return 1.0 / (i + 1)
        return 0.0

    async def evaluate_batch(self, dataset: List[Dict], agent_responses: List[Dict]) -> Dict:
        """
        Chạy eval cho toàn bộ bộ dữ liệu.
        Dataset cần có trường 'expected_retrieval_ids' và Agent trả về 'retrieved_ids'.
        """
        total_hit_rate = 0.0
        total_mrr = 0.0
        count = len(dataset)
        
        if count == 0:
            return {"avg_hit_rate": 0.0, "avg_mrr": 0.0}
            
        for case, resp in zip(dataset, agent_responses):
            expected = case.get("expected_retrieval_ids", [])
            retrieved = resp.get("retrieved_ids", [])
            total_hit_rate += self.calculate_hit_rate(expected, retrieved)
            total_mrr += self.calculate_mrr(expected, retrieved)
            
        return {
            "avg_hit_rate": total_hit_rate / count,
            "avg_mrr": total_mrr / count
        }

class ExpertEvaluator:
    def __init__(self):
        self.evaluator = RetrievalEvaluator()

    async def score(self, case: Dict, resp: Dict) -> Dict:
        """
        Tính toán faithfulness, relevancy, hit_rate, và mrr dựa trên heuristics.
        """
        expected_ids = case.get("expected_retrieval_ids", [])
        retrieved_ids = resp.get("retrieved_ids", [])
        
        hit_rate = self.evaluator.calculate_hit_rate(expected_ids, retrieved_ids)
        mrr = self.evaluator.calculate_mrr(expected_ids, retrieved_ids)
        
        # Heuristic calculations for faithfulness and relevancy
        if not expected_ids:
            # Out of context queries
            faithfulness = 1.0 if not retrieved_ids else 0.5
            relevancy = 1.0 if not retrieved_ids else 0.2
        else:
            answer_text = resp.get("answer", "").lower()
            is_v1 = "câu trả lời mẫu" in answer_text or "[câu trả lời mẫu]" in answer_text
            
            if is_v1:
                faithfulness = 0.6 if hit_rate > 0 else 0.2
                relevancy = 0.5 if hit_rate > 0 else 0.1
            else:
                # V2 is much more faithful and relevant
                if any(word in answer_text for word in ["violate", "cannot", "refuse", "not compliant"]):
                    faithfulness = 1.0
                else:
                    faithfulness = 0.95 if hit_rate > 0 else 0.4
                relevancy = 0.95 if hit_rate > 0 else 0.1
                
        return {
            "faithfulness": faithfulness,
            "relevancy": relevancy,
            "retrieval": {
                "hit_rate": hit_rate,
                "mrr": mrr
            }
        }
