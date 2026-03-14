import json
from groq import Groq

# ============================================================
# CONFIGURATION
# ============================================================

client = Groq(api_key="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")

MODEL = "llama-3.3-70b-versatile"

# ============================================================
# FUNCTION 1: GENERATE MILESTONES
# Input:  project_description (str), total_budget (float)
# Output: list of milestone dicts
# ============================================================

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


# ============================================================
# FUNCTION 2: EVALUATE WORK
# Input:  milestone (dict), submitted_work (str)
# Output: evaluation dict with verdict, score, feedback
# ============================================================
def evaluate_work(milestone, submitted_work):

    # ── Python detects vague/incomplete BEFORE calling AI ──
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

    # Hard cap scores before even calling AI
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

    # ── Only reach here if submission looks substantial ──
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

        # ── Score calculated in Python ──
        total = max(analysis.get("criteria_total", 1), 1)
        met = min(analysis.get("criteria_met", 0), total)
        score = int((met / total) * 100)

        if not analysis.get("has_evidence"):
            score = int(score * 0.55)

        if analysis.get("client_approved"):
            score = min(score + 10, 100)

        # Verdict from score
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
# ============================================================
# FUNCTION 3: CALCULATE PFI
# Input:  freelancer_history (dict)
# Output: pfi dict with score, grade, breakdown, recommendation
# ============================================================

def calculate_pfi(freelancer_history):
    prompt = f"""
    You are a reputation scoring AI for a freelance platform.
    
    Calculate a Professional Fidelity Index (PFI) score for this freelancer.
    
    Freelancer History:
    {json.dumps(freelancer_history, indent=2)}
    
    Return ONLY a JSON object, no extra text, no markdown:
    {{
        "pfi_score": <number from 0 to 100>,
        "grade": "A" or "B" or "C" or "D" or "F",
        "breakdown": {{
            "milestone_accuracy": <0 to 100>,
            "deadline_adherence": <0 to 100>,
            "work_quality": <0 to 100>
        }},
        "summary": "2 sentence summary of this freelancer's performance",
        "recommendation": "hire" or "caution" or "avoid"
    }}
    
    Scoring Rules:
    - milestone_accuracy: how often they fully complete milestones
    - deadline_adherence: how often they meet deadlines
    - work_quality: average score across all submissions
    - pfi_score = (milestone_accuracy * 0.4) + (deadline_adherence * 0.3) + (work_quality * 0.3)
    - A = 80-100, B = 65-79, C = 50-64, D = 35-49, F = below 35
    - recommendation: hire if A or B, caution if C, avoid if D or F
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        pfi = json.loads(raw)
        return {"success": True, "data": pfi}
    except json.JSONDecodeError:
        return {"success": False, "error": "AI returned invalid format"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# QUICK TEST — delete this block before handing to teammate
# ============================================================

if __name__ == "__main__":

    print("=" * 50)
    print("TEST 1: GENERATE MILESTONES")
    print("=" * 50)
    project = "Build a portfolio website with 5 pages, contact form, and mobile responsiveness"
    budget = 500
    result = generate_milestones(project, budget)
    if result["success"]:
        for m in result["data"]:
            print(f"  Milestone {m['milestone_id']}: {m['title']} | {m['payment_percentage']}% | Day {m['deadline_days']}")
    else:
        print(f"  ERROR: {result['error']}")

    print()
    print("=" * 50)
    print("TEST 2: EVALUATE WORK")
    print("=" * 50)
    sample_milestone = {
        "title": "Plan and Design Website",
        "completion_criteria": "Client approves the website plan, designs, and color scheme in writing"
    }
    sample_submission = """
    I have completed the website design. Here is what I did:
    - Created wireframes for all 5 pages
    - Designed the homepage layout with hero section
    - Chose color scheme: blue and white
    - Client has not approved yet, waiting for response
    """
    result = evaluate_work(sample_milestone, sample_submission)
    if result["success"]:
        d = result["data"]
        print(f"  Verdict  : {d['verdict'].upper()}")
        print(f"  Score    : {d['score']}/100")
        print(f"  Feedback : {d['feedback']}")
        print(f"  Release  : {d['release_payment']}")
    else:
        print(f"  ERROR: {result['error']}")

    print()
    print("=" * 50)
    print("TEST 3: CALCULATE PFI")
    print("=" * 50)
    history = {
        "freelancer_id": "FL001",
        "name": "Alex Johnson",
        "total_projects": 5,
        "milestones": [
            {"title": "Homepage Design",      "verdict": "completed", "score": 92, "met_deadline": True},
            {"title": "Backend API",           "verdict": "completed", "score": 88, "met_deadline": True},
            {"title": "Mobile UI",             "verdict": "partial",   "score": 65, "met_deadline": False},
            {"title": "Database Setup",        "verdict": "completed", "score": 90, "met_deadline": True},
            {"title": "Final Testing",         "verdict": "failed",    "score": 30, "met_deadline": False},
            {"title": "Landing Page",          "verdict": "completed", "score": 85, "met_deadline": True},
            {"title": "Payment Integration",   "verdict": "completed", "score": 78, "met_deadline": True},
        ]
    }
    result = calculate_pfi(history)
    if result["success"]:
        d = result["data"]
        print(f"  PFI Score      : {d['pfi_score']}/100")
        print(f"  Grade          : {d['grade']}")
        print(f"  Recommendation : {d['recommendation'].upper()}")
        print(f"  Summary        : {d['summary']}")
    else:
        print(f"  ERROR: {result['error']}")
