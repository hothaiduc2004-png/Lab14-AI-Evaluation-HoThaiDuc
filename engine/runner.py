import asyncio
import time
from typing import List, Dict

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        """
        Chạy một test case đơn lẻ: Gọi Agent, Eval bằng Heuristic, và chấm điểm bằng Judge LLM.
        """
        start_time = time.perf_counter()
        
        # 1. Gọi RAG Agent (Giả định hàm async)
        # Truyền câu hỏi vào và nhận câu trả lời cùng metadata hệ thống
        response = await self.agent.answer(test_case["question"])
        
        latency = time.perf_counter() - start_time
        
        # 2. Chạy bộ Eval Heuristic (Lớp ExpertEvaluator đã sửa từ bài trước)
        ragas_scores = await self.evaluator.score(test_case, response)
        
        # 3. Gọi Judge LLM để chấm điểm cuối cùng (Giả định hàm async)
        judge_result = await self.judge.evaluate_answer(
            test_case["question"], 
            response["answer"], 
            test_case["expected_answer"]
        )
        
        # 4. Token & Cost tracking
        # Tính toán chi phí cho Agent
        prompt_tokens = response["metadata"].get("prompt_tokens", 150)
        completion_tokens = response["metadata"].get("completion_tokens", 90)
        agent_model = response["metadata"].get("model", "gpt-4o-mini")
        
        if "mini" in agent_model:
            agent_cost = (prompt_tokens * 0.15 / 1e6) + (completion_tokens * 0.60 / 1e6)
        else:
            agent_cost = (prompt_tokens * 2.50 / 1e6) + (completion_tokens * 10.00 / 1e6)
            
        # Chi phí của Judge LLMs (Simulated token sizes for evaluations)
        # Judge A (gpt-4o): 400 prompt, 80 completion
        judge_a_cost = (400 * 2.50 / 1e6) + (80 * 10.00 / 1e6) # $0.0018
        
        # Judge B (claude-3-5): 450 prompt, 90 completion
        judge_b_cost = (450 * 3.00 / 1e6) + (90 * 15.00 / 1e6) # $0.0027
        
        judge_tokens = 400 + 80 + 450 + 90
        judge_cost = judge_a_cost + judge_b_cost
        
        # Judge C (gemini-1.5-pro) tham gia nếu có conflict giữa A và B
        if judge_result.get("conflict_resolved", False):
            judge_c_cost = (1000 * 1.25 / 1e6) + (120 * 5.00 / 1e6) # $0.00185
            judge_cost += judge_c_cost
            judge_tokens += 1000 + 120
            
        total_tokens = prompt_tokens + completion_tokens + judge_tokens
        total_cost = agent_cost + judge_cost
        
        # 5. Xác định Status (Pass / Fail) dựa trên điều kiện logic
        status = "pass"
        expected_ids = test_case.get("expected_retrieval_ids", [])
        hit_rate = ragas_scores["retrieval"]["hit_rate"]
        
        # Điều kiện fail: Điểm cuối của Judge < 3.5 HOẶC query cần context nhưng tìm kiếm hụt (hit_rate == 0)
        if judge_result.get("final_score", 0) < 3.5:
            status = "fail"
        elif expected_ids and hit_rate == 0.0:
            status = "fail"
            
        return {
            "test_case": test_case["question"],
            "agent_response": response["answer"],
            "expected_answer": test_case["expected_answer"],
            "difficulty": test_case["metadata"].get("difficulty", "medium"),
            "category": test_case["metadata"].get("category", "general"),
            "latency": latency,
            "ragas": ragas_scores,
            "judge": judge_result,
            "tokens_used": total_tokens,
            "cost_usd": total_cost,
            "status": status
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 15) -> List[Dict]:
        """
        Chạy song song toàn bộ dữ liệu bằng asyncio.gather kết hợp Semaphore 
        để kiểm soát số lượng request đồng thời (Tránh dính Rate Limit).
        """
        semaphore = asyncio.Semaphore(batch_size)
        
        async def sem_run(test_case):
            async with semaphore:
                return await self.run_single_test(test_case)
                
        tasks = [sem_run(case) for case in dataset]
        return await asyncio.gather(*tasks)
