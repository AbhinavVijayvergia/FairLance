import json
from groq import Groq

client = Groq(api_key="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")

MODEL = "llama-3.3-70b-versatile"


def generate_milestones(project_description, total_budget):
    prompt = f"""
    You are a project management AI for a freelance platform.
    
    Analyze this project and break it into 3-5 milestones.
    
    Project: {project_description}
    Total Budget: ${total_budget}
    
    Return ONLY a JSON array, no extra text, no markdown, just pure JSON like this:
    [
        {{
            "milestone_id": 1,
            "title": "milestone title",
            "description": "what needs to be done",
            "completion_criteria": "how we know it's done",
            "payment_percentage": 20,
            "deadline_days": 3
        }}
    ]
    
    Rules:
    - payment_percentage across all milestones must add up to exactly 100
    - deadline_days is number of days from project start
    - be specific and measurable in completion_criteria
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        milestones = json.loads(raw)
        return {"success": True, "data": milestones}
    except json.JSONDecodeError:
        return {"success": False, "error": "AI returned invalid format"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def evaluate_work(milestone, submitted_work):

    work_lower = submitted_work.lower().strip()

    vague_phrases = [
        "will do", "will submit", "not finished", "not done", "in progress",
        "working on it", "coming soon", "will complete", "haven't", "have not",
        "not yet", "soon", "later", "pending", "incomplete", "not started",
        "will send", "almost done", "nearly done", "not ready"
    ]

    is_incomplete = any(phrase in work_lower for phrase in vague_phrases)
    is_too_short = len(submitted_work.strip()) < 80
    is_vague = is_incomplete or is_too_short

    if is_incomplete:
        return {
            "success": True,
            "data": {
                "verdict": "failed",
                "score": 15,
                "feedback": "Submission indicates work is not yet complete. Payment cannot be released until all milestone criteria are fully delivered. Please resubmit once the work is finished.",
                "release_payment": False,
                "partial_payment_percentage": 0
            }
        }

    if is_too_short:
        return {
            "success": True,
            "data": {
                "verdict": "failed",
                "score": 20,
                "feedback": "Submission is too vague and lacks sufficient detail. Please provide specific deliverables, links, or evidence that each completion criterion has been met.",
                "release_payment": False,
                "partial_payment_percentage": 0
            }
        }

    prompt = f"""
    You are a strict project quality evaluator for a freelance platform.
    
    Milestone Title: {milestone['title']}
    Completion Criteria: {milestone['completion_criteria']}
    
    Freelancer's Submitted Work:
    {submitted_work}
    
    Return ONLY a JSON object, no extra text, no markdown:
    {{
        "criteria_met": <integer, how many criteria points are explicitly proven>,
        "criteria_total": <integer, total criteria points in the criteria text>,
        "has_evidence": true or false,
        "client_approved": true or false,
        "feedback": "specific feedback on what was done well and what is missing"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        analysis = json.loads(raw)

        total = max(analysis.get("criteria_total", 1), 1)
        met = min(analysis.get("criteria_met", 0), total)
        score = int((met / total) * 100)

        if not analysis.get("has_evidence"):
            score = int(score * 0.55)

        if analysis.get("client_approved"):
            score = min(score + 10, 100)

        if score >= 80:
            verdict = "completed"
            release_payment = True
            partial_pct = 100
        elif score >= 40:
            verdict = "partial"
            release_payment = False
            partial_pct = score
        else:
            verdict = "failed"
            release_payment = False
            partial_pct = 0

        return {
            "success": True,
            "data": {
                "verdict": verdict,
                "score": score,
                "feedback": analysis.get("feedback", ""),
                "release_payment": release_payment,
                "partial_payment_percentage": partial_pct
            }
        }

    except json.JSONDecodeError:
        return {"success": False, "error": "AI returned invalid format"}
    except Exception as e:
        return {"success": False, "error": str(e)}
