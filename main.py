import asyncio
import json
import os
import time
import sys
from typing import List, Dict

# Reconfigure stdout to use UTF-8 on Windows to avoid encoding errors on print
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import các components thực tế từ project của bạn
# từ engine.runner import BenchmarkRunner
# từ agent.main_agent import MainAgent
# từ engine.retrieval_eval import ExpertEvaluator
# từ engine.llm_judge import LLMJudge

# --- MOCK COMPONENTS (Thay thế bằng class thật của bạn nếu cần) ---
class MainAgent:
    def __init__(self, version: str = "Base"):
        self.version = version
    async def answer(self, question: str):
        await asyncio.sleep(0.1) # Giả lập latency
        return {
            "answer": f"Answer from {self.version}",
            "metadata": {"prompt_tokens": 200, "completion_tokens": 100, "model": "gpt-4o-mini"}
        }

class ExpertEvaluator:
    def score(self, case, resp): 
        return {
            "faithfulness": 0.9, 
            "relevancy": 0.8,
            "retrieval": {"hit_rate": 1.0, "mrr": 0.5}
        }

class LLMJudge:
    async def evaluate_answer(self, q, a, gt): 
        return {
            "final_score": 4.5, 
            "agreement_rate": 0.8,
            "conflict_resolved": False,
            "reasoning": "Cả 2 model đồng ý đây là câu trả lời tốt."
        }

class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        response = await self.agent.answer(test_case["question"])
        latency = time.perf_counter() - start_time
        
        ragas_scores = self.evaluator.score(test_case, response)
        judge_result = await self.judge.evaluate_answer(
            test_case["question"], response["answer"], test_case["expected_answer"]
        )
        
        # Token & Cost tracking
        prompt_tokens = response["metadata"].get("prompt_tokens", 150)
        completion_tokens = response["metadata"].get("completion_tokens", 90)
        agent_cost = (prompt_tokens * 0.15 / 1e6) + (completion_tokens * 0.60 / 1e6)
        judge_cost = (400 * 2.50 / 1e6) + (80 * 10.00 / 1e6) + (450 * 3.00 / 1e6) + (90 * 15.00 / 1e6)
        
        return {
            "test_case": test_case["question"],
            "agent_response": response["answer"],
            "expected_answer": test_case["expected_answer"],
            "difficulty": test_case["metadata"].get("difficulty", "medium"),
            "category": test_case["metadata"].get("category", "general"),
            "latency": latency,
            "ragas": ragas_scores,
            "judge": judge_result,
            "tokens_used": prompt_tokens + completion_tokens + 1020,
            "cost_usd": agent_cost + judge_cost,
            "status": "pass" if judge_result["final_score"] >= 3.5 else "fail"
        }

    async def run_all(self, dataset: List[Dict], batch_size: int = 15) -> List[Dict]:
        semaphore = asyncio.Semaphore(batch_size)
        async def sem_run(case):
            async with semaphore:
                return await self.run_single_test(case)
        tasks = [sem_run(case) for case in dataset]
        return await asyncio.gather(*tasks)

# --- MAIN BENCHMARK LOGIC ---

async def run_benchmark_with_results(agent_version: str):
    print(f"🚀 Khởi động Benchmark cho {agent_version}...")

    # Logic đọc dữ liệu từ file golden_set.jsonl thực tế
    dataset = []
    file_path = "data/golden_set.jsonl"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    dataset.append(json.loads(line))
                    
    if not dataset:
        print("❌ File data/golden_set.jsonl rỗng hoặc không tồn tại. Hãy tạo ít nhất 1 test case.")
        return None, None

    # Khởi tạo các components thực tế
    agent = MainAgent(version=agent_version)
    evaluator = ExpertEvaluator()
    judge = LLMJudge()
    
    runner = BenchmarkRunner(agent, evaluator, judge)
    results = await runner.run_all(dataset, batch_size=15)

    total = len(results)
    avg_score = sum(r["judge"]["final_score"] for r in results) / total
    hit_rate = sum(r["ragas"]["retrieval"]["hit_rate"] for r in results) / total
    mrr = sum(r["ragas"]["retrieval"]["mrr"] for r in results) / total
    agreement_rate = sum(r["judge"]["agreement_rate"] for r in results) / total
    avg_latency = sum(r["latency"] for r in results) / total
    total_tokens = sum(r["tokens_used"] for r in results)
    total_cost = sum(r["cost_usd"] for r in results)
    pass_count = sum(1 for r in results if r["status"] == "pass")
    pass_rate = pass_count / total

    summary = {
        "metadata": {
            "version": agent_version, 
            "total": total, 
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "metrics": {
            "avg_score": avg_score,
            "hit_rate": hit_rate,
            "mrr": mrr,
            "agreement_rate": agreement_rate,
            "avg_latency": avg_latency,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_cost_per_query_usd": total_cost / total,
            "pass_rate": pass_rate,
            "pass_count": pass_count
        }
    }
    return results, summary

async def run_benchmark(version):
    _, summary = await run_benchmark_with_results(version)
    return summary

async def main():
    start_time = time.time()
    
    # 1. Run Benchmark for V1 (Base)
    v1_summary = await run_benchmark("Agent_V1_Base")
    
    # 2. Run Benchmark for V2 (Optimized)
    v2_results, v2_summary = await run_benchmark_with_results("Agent_V2_Optimized")
    
    if not v1_summary or not v2_summary:
        print("❌ Không thể chạy Benchmark. Kiểm tra lại data/golden_set.jsonl.")
        return

    duration = time.time() - start_time
    print(f"\n⚡ Toàn bộ Benchmark chạy trong {duration:.2f} giây.")

    print("\n📊 --- KẾT QUẢ SO SÁNH (REGRESSION) ---")
    delta_score = v2_summary["metrics"]["avg_score"] - v1_summary["metrics"]["avg_score"]
    delta_hit_rate = v2_summary["metrics"]["hit_rate"] - v1_summary["metrics"]["hit_rate"]
    
    print(f"🔹 Version 1 (Base):")
    print(f"   - Score: {v1_summary['metrics']['avg_score']:.2f}")
    print(f"   - Hit Rate: {v1_summary['metrics']['hit_rate']*100:.1f}%")
    print(f"   - MRR: {v1_summary['metrics']['mrr']:.2f}")
    print(f"   - Latency: {v1_summary['metrics']['avg_latency']:.2f}s")
    print(f"   - Total Cost: ${v1_summary['metrics']['total_cost_usd']:.4f}")
    
    print(f"🔹 Version 2 (Optimized):")
    print(f"   - Score: {v2_summary['metrics']['avg_score']:.2f} (Delta: {delta_score:+.2f})")
    print(f"   - Hit Rate: {v2_summary['metrics']['hit_rate']*100:.1f}% (Delta: {delta_hit_rate*100:+.1f}%)")
    print(f"   - MRR: {v2_summary['metrics']['mrr']:.2f}")
    print(f"   - Latency: {v2_summary['metrics']['avg_latency']:.2f}s")
    print(f"   - Total Cost: ${v2_summary['metrics']['total_cost_usd']:.4f}")

    # Auto-Gate Decision Logic
    score_improved = delta_score > 0
    score_ok = v2_summary["metrics"]["avg_score"] >= 4.0
    hit_rate_ok = v2_summary["metrics"]["hit_rate"] >= 0.85
    latency_ok = v2_summary["metrics"]["avg_latency"] <= 0.5

    gate_approved = score_improved and score_ok and hit_rate_ok and latency_ok

    print("\n🚧 --- REGRESSION RELEASE GATE DECISION ---")
    print(f"1. Score Improvement (Delta > 0):   {'✅' if score_improved else '❌'} ({delta_score:+.2f})")
    print(f"2. Quality Target (Score >= 4.0):    {'✅' if score_ok else '❌'} ({v2_summary['metrics']['avg_score']:.2f})")
    print(f"3. Retrieval Target (Hit Rate >= 85%): {'✅' if hit_rate_ok else '❌'} ({v2_summary['metrics']['hit_rate']*100:.1f}%)")
    print(f"4. Latency Target (<= 0.5s):        {'✅' if latency_ok else '❌'} ({v2_summary['metrics']['avg_latency']:.2f}s)")

    v2_summary["gate_decision"] = "APPROVED" if gate_approved else "BLOCKED"

    # Ghi báo cáo ra file json
    os.makedirs("reports", exist_ok=True)
    with open("reports/summary.json", "w", encoding="utf-8") as f:
        json.dump(v2_summary, f, ensure_ascii=False, indent=2)
    with open("reports/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(v2_results, f, ensure_ascii=False, indent=2)

    # In kết quả quyết định Gate cuối cùng trực quan
    if gate_approved:
        print("\n🏆 [GATE DECISION: APPROVED] - Bản cập nhật đạt tiêu chuẩn phát hành!")
    else:
        print("\n🛑 [GATE DECISION: BLOCKED] - Bản cập nhật bị chặn do không đạt tiêu chuẩn chất lượng/hiệu năng.")

if __name__ == "__main__":
    # Tạo sẵn thư mục data/ và file mẫu nếu chưa có để chạy không lỗi
    os.makedirs("data", exist_ok=True)
    if not os.path.exists("data/golden_set.jsonl"):
        with open("data/golden_set.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"question": "Test q?", "expected_answer": "Test a.", "metadata": {}}) + "\n")
            
    asyncio.run(main())
