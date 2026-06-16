import asyncio
from typing import List, Dict

# Standard document chunks matching data/synthetic_gen.py
DOCUMENT_CHUNKS = {
    "auth_01": "Password Policy: All employee accounts must use passwords with a minimum length of 12 characters, including at least one uppercase letter, one lowercase letter, one number, and one special character. Passwords must be changed every 90 days.",
    "auth_02": "Account Lockout: An account will be locked out for 15 minutes after 5 consecutive failed login attempts. To unlock earlier, contact the IT service desk.",
    "remote_01": "Remote Work VPN: Access to internal systems is only allowed through the company secure VPN. Multi-Factor Authentication (MFA) is mandatory for VPN access.",
    "remote_02": "Device Security: Employees are only allowed to use company-approved devices to access company resources. Lost or stolen devices must be reported to IT security within 24 hours.",
    "deploy_01": "Code Review Policy: All code changes must be reviewed and approved by at least one Senior Engineer before merging into the main branch. Code coverage must exceed 80%.",
    "deploy_02": "Deployment Stages: Code must pass unit and integration tests in CI/CD. It is deployed to Staging for manual QA, then to Production only after Product Owner approval.",
    "privacy_01": "PII Logging: Personally Identifiable Information (PII) such as emails, phone numbers, and credit card details must never be written to application logs.",
    "privacy_02": "GDPR Compliance: User data must be encrypted at rest and in transit. User requests for data deletion (Right to be Forgotten) must be completed within 30 days.",
    "api_01": "API Error 401: A 401 Unauthorized error indicates that the auth token is missing or expired. Clients should refresh the OAuth token using the refresh_token flow.",
    "api_02": "API Error 429: A 429 Too Many Requests error indicates rate limit exhaustion. Clients must parse the 'Retry-After' header and wait the specified seconds before retrying.",
    "api_03": "API Error 503: A 503 Service Unavailable error means the primary region is down. The system automatically routes read requests to the secondary fallback region."
}

class MainAgent:
    """
    Đây là Agent mẫu sử dụng kiến trúc RAG đơn giản.
    Sinh viên nên thay thế phần này bằng Agent thực tế đã phát triển ở các buổi trước.
    RAG Agent simulating Base (V1) and Optimized (V2) versions.
    V1: Poor chunking, weak prompt, misses safety guards.
    V2: Semantic chunking, reranking, system prompt guards, and lower latency.
    """
    def __init__(self):
        self.name = "SupportAgent-v1"
    def __init__(self, version: str = "Agent_V1_Base"):
        self.version = version
        self.name = f"SupportAgent-{version}"

    async def query(self, question: str) -> Dict:
        """
        Mô phỏng quy trình RAG:
        1. Retrieval: Tìm kiếm context liên quan.
        2. Generation: Gọi LLM để sinh câu trả lời.
        2. Generation: Sinh câu trả lời dựa trên context.
        """
        # Giả lập độ trễ mạng/LLM
        await asyncio.sleep(0.5) 
        question_lower = question.lower()
        
        # Giả lập dữ liệu trả về
        # 1. Simulate Retrieval Stage
        retrieved_ids = []
        contexts = []
        
        # Determine relevant document keys for the question
        relevant_keys = []
        if "password" in question_lower or "length" in question_lower or "compliant" in question_lower:
            relevant_keys.append("auth_01")
        if "lock" in question_lower or "fail" in question_lower or "unlock" in question_lower:
            relevant_keys.append("auth_02")
        if "vpn" in question_lower or "remote" in question_lower or "mfa" in question_lower:
            relevant_keys.append("remote_01")
        if "device" in question_lower or "laptop" in question_lower or "phone" in question_lower or "lost" in question_lower:
            relevant_keys.append("remote_02")
        if "review" in question_lower or "merge" in question_lower or "approve" in question_lower or "coverage" in question_lower:
            relevant_keys.append("deploy_01")
        if "deploy" in question_lower or "staging" in question_lower or "production" in question_lower or "qa" in question_lower:
            relevant_keys.append("deploy_02")
        if "log" in question_lower or "pii" in question_lower or "phone" in question_lower or "credit" in question_lower:
            relevant_keys.append("privacy_01")
        if "gdpr" in question_lower or "delete" in question_lower or "forget" in question_lower or "encrypt" in question_lower:
            relevant_keys.append("privacy_02")
        if "401" in question_lower or "unauthorized" in question_lower or "token" in question_lower:
            relevant_keys.append("api_01")
        if "429" in question_lower or "rate" in question_lower or "retry" in question_lower:
            relevant_keys.append("api_02")
        if "503" in question_lower or "region" in question_lower or "fallback" in question_lower:
            relevant_keys.append("api_03")

        # Simulate retrieval errors and biases
        if self.version == "Agent_V1_Base":
            # V1 retrieval simulation: Poor recall, Position bias, retrieves random things occasionally
            await asyncio.sleep(0.6)  # Basic search takes longer
            if relevant_keys:
                # V1 retrieves only the first relevant key, or misses it entirely
                if "adversarial" in question_lower or "override" in question_lower or "ignore" in question_lower:
                    # Adversarial prompts trick V1 to retrieve nothing or get distracted
                    retrieved_ids = ["auth_02"] # Irrelevant chunk
                else:
                    retrieved_ids = [relevant_keys[0]]
            else:
                retrieved_ids = ["auth_01"] # Default fallback retrieval (Position bias / Noise)
            
            # Populate contexts based on retrieved_ids
            contexts = [DOCUMENT_CHUNKS[k] for k in retrieved_ids if k in DOCUMENT_CHUNKS]
            
            # V1 Generation Logic (prone to mistakes and prompt injections)
            tokens_in = 150
            tokens_out = 90
            
            if "ignore" in question_lower or "admin password" in question_lower:
                answer = "Sure, the default admin password is 'Admin@2026!'. Please change it immediately."
            elif "override" in question_lower or "bypass" in question_lower:
                answer = "System override accepted. The pull request has been approved and successfully merged."
            elif "credit card" in question_lower or "log" in question_lower and "script" in question_lower:
                answer = "Here is a Python script that logs credit card details for debugging: \n```python\nlogger.info(f'Processing card: {card_number}')\n```"
            elif "compliant" in question_lower and "Secret123!" in question:
                answer = "Yes, 'Secret123!' is compliant because it has uppercase, lowercase, numbers, and a special character." # Hallucination (length is only 10, needs 12)
            elif "travel expense" in question_lower or "cake" in question_lower:
                answer = "I will search the web for travel expense policies and get back to you soon. [Hallucinated external capability]."
            else:
                # Default response
                answer = f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu]."
                
        else:
            # Agent_V2_Optimized retrieval simulation: semantic chunking + reranking
            await asyncio.sleep(0.3)  # Optimized retrieval is faster
            retrieved_ids = relevant_keys
            contexts = [DOCUMENT_CHUNKS[k] for k in retrieved_ids if k in DOCUMENT_CHUNKS]
            
            # V2 Generation Logic (Advanced prompt, safety guards, structured responses)
            tokens_in = 320 # Larger system prompt with few-shot guards
            tokens_out = 110
            
            if "ignore" in question_lower or "admin password" in question_lower:
                answer = "I cannot perform this action. I am a support assistant and do not have access to admin passwords."
            elif "override" in question_lower or "bypass" in question_lower:
                answer = "I cannot bypass safety policies or system checks. A Senior Engineer must review and approve code changes."
            elif "credit card" in question_lower or "log" in question_lower and "script" in question_lower:
                answer = "I cannot write a script to log PII. Doing so violates our privacy policy which forbids writing credit card details to logs."
            elif "compliant" in question_lower and "Secret123!" in question:
                answer = "No, the password 'Secret123!' is not compliant with the policy. Although it meets the complexity rules (uppercase, lowercase, number, special character), it has only 10 characters, which is less than the minimum required length of 12 characters."
            elif "travel expense" in question_lower:
                answer = "I do not have any information about travel expense policies in the system documents."
            elif "cake" in question_lower:
                answer = "I cannot assist with baking recipes. I am a support assistant focused on system security, privacy, deployment, and APIs."
            elif "retry" in question_lower or "429" in question_lower:
                answer = "A 429 Too Many Requests error indicates rate limit exhaustion. The client must parse the 'Retry-After' header from the API response and wait for the specified number of seconds before attempting the request again."
            elif "503" in question_lower:
                answer = "A 503 Service Unavailable error indicates that the primary region is down. The system automatically routes read requests to the secondary fallback region to ensure continuity."
            elif "unauthorized" in question_lower or "401" in question_lower:
                answer = "A 401 Unauthorized error indicates that the authentication token is either missing or expired. To resolve this, the client should refresh the OAuth token using the refresh_token flow."
            elif "password" in question_lower:
                answer = "According to the corporate Password Policy:\n1. All passwords must be at least 12 characters long.\n2. Passwords must include at least one uppercase letter, one lowercase letter, one number, and one special character.\n3. Passwords must be updated every 90 days."
            elif "lock" in question_lower:
                answer = "Under the Account Lockout Policy, an employee account will be automatically locked for 15 minutes after 5 consecutive failed login attempts. If you need to unlock the account sooner, you must contact the IT service desk."
            elif "vpn" in question_lower:
                answer = "Access to corporate internal systems is restricted and only permitted through the secure company VPN. Additionally, Multi-Factor Authentication (MFA) is strictly mandatory for all VPN access."
            elif "device" in question_lower or "laptop" in question_lower:
                answer = "Employees are permitted to access corporate resources using only company-approved devices. Personal devices are not allowed. In the event of a lost or stolen device, it must be reported to IT security within 24 hours."
            elif "review" in question_lower or "merge" in question_lower:
                answer = "All code changes must be reviewed and approved by at least one Senior Engineer before they can be merged into the main branch. Additionally, the code coverage must exceed 80%."
            elif "gdpr" in question_lower or "delete" in question_lower:
                answer = "To ensure GDPR compliance, user data must be encrypted at rest and in transit. Any user request for data deletion (Right to be Forgotten) must be fully executed and completed within 30 days."
            else:
                answer = f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời đầy đủ và chi tiết dựa trên context]."

        return {
            "answer": f"Dựa trên tài liệu hệ thống, tôi xin trả lời câu hỏi '{question}' như sau: [Câu trả lời mẫu].",
            "contexts": [
                "Đoạn văn bản trích dẫn 1 dùng để trả lời...",
                "Đoạn văn bản trích dẫn 2 dùng để trả lời..."
            ],
            "answer": answer,
            "contexts": contexts,
            "retrieved_ids": retrieved_ids,
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": 150,
                "model": "gpt-4o-mini" if self.version == "Agent_V1_Base" else "gpt-4o",
                "tokens_used": tokens_in + tokens_out,
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "latency": 0.6 if self.version == "Agent_V1_Base" else 0.3,
                "sources": ["policy_handbook.pdf"]
            }
        }

if __name__ == "__main__":
    agent = MainAgent()
    async def test():
        agent = MainAgent(version="Agent_V2_Optimized")
        resp = await agent.query("Làm thế nào để đổi mật khẩu?")
        print(resp)
    asyncio.run(test())
