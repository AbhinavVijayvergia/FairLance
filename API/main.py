from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai_agent import generate_milestones, evaluate_work, calculate_pfi
from database import Base, engine, get_db, SessionLocal
from models import Project as ProjectModel, Submission as SubmissionModel, Milestone as MilestoneModel


app = FastAPI()


# Create tables on startup (simple approach for this small project)
Base.metadata.create_all(bind=engine)


def seed_demo_data():
    """
    Seed a couple of demo projects + milestones so the freelancer
    dashboard has something to show even before any employer posts.
    Only runs when there are zero projects.
    """
    db = SessionLocal()
    try:
        if db.query(ProjectModel).count() > 0:
            return

        demo_projects = [
            {
                "title": "Portfolio Website (5 pages)",
                "description": "Design and build a modern responsive portfolio website with 5 pages and a contact form.",
                "budget": 500,
                "milestones": [
                    {
                        "milestone_id": 1,
                        "title": "Plan & Design",
                        "description": "Wireframes, design system, and client-approved layout.",
                        "completion_criteria": "Client approves all page wireframes and visual direction in writing.",
                        "payment_percentage": 20,
                        "deadline_days": 3,
                    },
                    {
                        "milestone_id": 2,
                        "title": "Core Development",
                        "description": "Build all 5 pages with responsive layout.",
                        "completion_criteria": "All pages implemented, navigation working, content populated.",
                        "payment_percentage": 50,
                        "deadline_days": 7,
                    },
                    {
                        "milestone_id": 3,
                        "title": "Forms, QA & Launch",
                        "description": "Contact form, final QA, and deployment.",
                        "completion_criteria": "Form sends emails, site deployed, and no critical bugs.",
                        "payment_percentage": 30,
                        "deadline_days": 10,
                    },
                ],
            },
            {
                "title": "Landing Page with A/B Test",
                "description": "High-conversion landing page build with two variants for A/B testing.",
                "budget": 800,
                "milestones": [
                    {
                        "milestone_id": 1,
                        "title": "Copy & Wireframes",
                        "description": "Define messaging and rough layout.",
                        "completion_criteria": "Approved copy document and low-fidelity wireframes.",
                        "payment_percentage": 25,
                        "deadline_days": 2,
                    },
                    {
                        "milestone_id": 2,
                        "title": "Variant A & B Build",
                        "description": "Implement both variants in code.",
                        "completion_criteria": "Two live variants accessible via toggle, pixel-perfect to designs.",
                        "payment_percentage": 50,
                        "deadline_days": 6,
                    },
                    {
                        "milestone_id": 3,
                        "title": "Analytics & Handoff",
                        "description": "Hook up analytics and document experiment setup.",
                        "completion_criteria": "Tracking installed and handoff doc with experiment instructions.",
                        "payment_percentage": 25,
                        "deadline_days": 9,
                    },
                ],
            },
            {
                "title": "API Integration for Payments",
                "description": "Integrate a payment provider (Stripe-like) into an existing app.",
                "budget": 1200,
                "milestones": [
                    {
                        "milestone_id": 1,
                        "title": "Design Payment Flow",
                        "description": "Define endpoints and UX flow.",
                        "completion_criteria": "Sequence diagrams and API contract approved.",
                        "payment_percentage": 20,
                        "deadline_days": 3,
                    },
                    {
                        "milestone_id": 2,
                        "title": "Implement Core Charges",
                        "description": "Charging, refunds, and error handling.",
                        "completion_criteria": "Successful test payments, refunds, and error cases covered.",
                        "payment_percentage": 50,
                        "deadline_days": 8,
                    },
                    {
                        "milestone_id": 3,
                        "title": "Security & Documentation",
                        "description": "Harden security and write docs.",
                        "completion_criteria": "Security checklist complete and integration guide delivered.",
                        "payment_percentage": 30,
                        "deadline_days": 12,
                    },
                ],
            },
        ]

        for proj in demo_projects:
            db_project = ProjectModel(
                title=proj["title"],
                description=proj["description"],
                budget=proj["budget"],
            )
            db.add(db_project)
            db.commit()
            db.refresh(db_project)

            for m in proj["milestones"]:
                db_milestone = MilestoneModel(
                    project_id=db_project.id,
                    milestone_id=m["milestone_id"],
                    title=m["title"],
                    description=m["description"],
                    completion_criteria=m["completion_criteria"],
                    payment_percentage=m["payment_percentage"],
                    deadline_days=m["deadline_days"],
                )
                db.add(db_milestone)

            db.commit()
    finally:
        db.close()


# Seed initial demo data if database is empty
seed_demo_data()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Project(BaseModel):
    title: str
    description: str
    budget: int


class ProjectResponse(Project):
    id: int

    class Config:
        orm_mode = True


class Submission(BaseModel):
    project_id: int
    milestone_id: int
    link: str


@app.post("/project/create")
def create_project(project: Project, db: Session = Depends(get_db)):
    """
    Create a project and persist it to the SQLite database.
    """
    db_project = ProjectModel(
        title=project.title,
        description=project.description,
        budget=project.budget,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return {
        "message": "Project created",
        "project": {
            "id": db_project.id,
            "title": db_project.title,
            "description": db_project.description,
            "budget": db_project.budget,
        },
    }


@app.post("/project/create-with-milestones")
def create_project_with_milestones(project: Project, db: Session = Depends(get_db)):
    """
    Create a project, have the AI generate milestones, persist everything,
    and return the full project payload including milestones.
    """
    db_project = ProjectModel(
        title=project.title,
        description=project.description,
        budget=project.budget,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    ai_result = generate_milestones(project.description, project.budget)
    if not ai_result["success"]:
        raise HTTPException(status_code=500, detail=ai_result["error"])

    milestones_payload = ai_result["data"]

    for m in milestones_payload:
        db_milestone = MilestoneModel(
            project_id=db_project.id,
            milestone_id=m.get("milestone_id"),
            title=m.get("title"),
            description=m.get("description"),
            completion_criteria=m.get("completion_criteria"),
            payment_percentage=m.get("payment_percentage"),
            deadline_days=m.get("deadline_days"),
        )
        db.add(db_milestone)

    db.commit()

    return {
        "project": {
            "id": db_project.id,
            "title": db_project.title,
            "description": db_project.description,
            "budget": db_project.budget,
        },
        "milestones": milestones_payload,
    }


@app.post("/project/create-from-milestones")
def create_project_from_milestones(payload: dict, db: Session = Depends(get_db)):
    """
    Create a project and persist a provided list of milestones (already generated
    by AI or using a fallback). This is used when the frontend first previews
    milestones, then the employer explicitly clicks "Post project".
    """
    title = payload.get("title") or ""
    description = payload.get("description") or ""
    budget = int(payload.get("budget") or 0)
    milestones_payload = payload.get("milestones") or []

    if not title or not description or budget <= 0 or not milestones_payload:
        raise HTTPException(status_code=400, detail="Invalid project or milestones payload")

    # Normalize milestones to avoid DB errors from missing fields / wrong types
    normalized_milestones = []
    for idx, raw in enumerate(milestones_payload, start=1):
        milestone_id = raw.get("milestone_id") or idx
        title_m = raw.get("title") or f"Milestone {milestone_id}"
        description_m = raw.get("description") or ""
        completion_criteria = raw.get("completion_criteria") or "Work submitted as required."
        try:
            payment_percentage = float(raw.get("payment_percentage") or 0)
        except (TypeError, ValueError):
            payment_percentage = 0.0
        try:
            deadline_days = int(raw.get("deadline_days") or (idx * 3))
        except (TypeError, ValueError):
            deadline_days = idx * 3

        normalized = {
            "milestone_id": milestone_id,
            "title": title_m,
            "description": description_m,
            "completion_criteria": completion_criteria,
            "payment_percentage": payment_percentage,
            "deadline_days": deadline_days,
        }
        normalized_milestones.append(normalized)

    db_project = ProjectModel(
        title=title,
        description=description,
        budget=budget,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    for m in normalized_milestones:
        db_milestone = MilestoneModel(
            project_id=db_project.id,
            milestone_id=m["milestone_id"],
            title=m["title"],
            description=m["description"],
            completion_criteria=m["completion_criteria"],
            payment_percentage=m["payment_percentage"],
            deadline_days=m["deadline_days"],
        )
        db.add(db_milestone)

    db.commit()

    return {
        "project": {
            "id": db_project.id,
            "title": db_project.title,
            "description": db_project.description,
            "budget": db_project.budget,
        },
        "milestones": normalized_milestones,
    }


@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    """
    Return all projects so freelancers can choose one.
    """
    projects = db.query(ProjectModel).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "budget": p.budget,
        }
        for p in projects
    ]


@app.get("/projects/{project_id}/milestones")
def list_milestones_for_project(project_id: int, db: Session = Depends(get_db)):
    """
    Return all milestones for a given project.
    """
    project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    milestones = (
        db.query(MilestoneModel)
        .filter(MilestoneModel.project_id == project_id)
        .order_by(MilestoneModel.milestone_id.asc())
        .all()
    )

    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "milestone_id": m.milestone_id,
            "title": m.title,
            "description": m.description,
            "completion_criteria": m.completion_criteria,
            "payment_percentage": m.payment_percentage,
            "deadline_days": m.deadline_days,
        }
        for m in milestones
    ]


@app.post("/ai/generate-milestones")
def ai_generate_milestones(project: Project):
    """
    Ask the Groq-powered AI agent to generate milestones.
    (Currently returns milestones but does not persist them;
    the UI focuses on display, not storage, for milestones.)
    """
    result = generate_milestones(project.description, project.budget)

    if result["success"]:
        return {
            "project": project.title,
            "milestones": result["data"],
        }
    else:
        return {
            "error": result["error"],
        }


@app.post("/milestone/submit")
def submit_work(data: Submission, db: Session = Depends(get_db)):
    """
    Store a raw milestone submission (before AI evaluation).
    """
    submission = SubmissionModel(
        project_id=data.project_id,
        milestone_id=data.milestone_id,
        work_link=data.link,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return {
        "message": "Work submitted successfully",
        "submission": {
            "id": submission.id,
            "project_id": submission.project_id,
            "milestone_id": submission.milestone_id,
            "link": submission.work_link,
        },
    }


@app.post("/verify/work")
def verify_work(data: Submission, db: Session = Depends(get_db)):
    """
    Verify submitted work using the AI agent and store the evaluation
    in the database. The response fields are shaped to match the
    expectations in Frontend/freelancer.html.
    """
    milestone_row = (
        db.query(MilestoneModel)
        .filter(
            MilestoneModel.project_id == data.project_id,
            MilestoneModel.milestone_id == data.milestone_id,
        )
        .first()
    )

    if milestone_row:
        milestone = {
            "title": milestone_row.title,
            "completion_criteria": milestone_row.completion_criteria,
        }
    else:
        milestone = {
            "title": "Milestone",
            "completion_criteria": "Work submitted as required",
        }

    result = evaluate_work(milestone, data.link)

    if not result["success"]:
        return {"error": result["error"]}

    evaluation = result["data"]

    # Upsert submission record
    submission = (
        db.query(SubmissionModel)
        .filter(
            SubmissionModel.project_id == data.project_id,
            SubmissionModel.milestone_id == data.milestone_id,
        )
        .first()
    )

    if not submission:
        submission = SubmissionModel(
            project_id=data.project_id,
            milestone_id=data.milestone_id,
            work_link=data.link,
        )
        db.add(submission)

    submission.verdict = evaluation.get("verdict")
    submission.score = evaluation.get("score")
    submission.feedback = evaluation.get("feedback")
    submission.release_payment = evaluation.get("release_payment")
    submission.partial_payment_percentage = evaluation.get("partial_payment_percentage")

    db.commit()

    # Shape response for the frontend
    return {
        "status": evaluation.get("verdict"),
        "quality_score": (evaluation.get("score") or 0) / 100.0,
        "feedback": evaluation.get("feedback"),
        "payment_released": evaluation.get("release_payment"),
        "partial_payment_percentage": evaluation.get("partial_payment_percentage") or 0,
    }


@app.post("/pfi/calculate")
def calculate_pfi_from_history(history: dict):
    """
    Calculate a PFI score from an arbitrary freelancer history payload.
    (Useful for API testing or future integrations.)
    """
    result = calculate_pfi(history)

    if result["success"]:
        return result["data"]
    else:
        return {"error": result["error"]}


@app.get("/pfi/{freelancer_id}")
def get_pfi_profile(freelancer_id: str):
    """
    Return a PFI profile shaped for Frontend/profile.html.
    For now this uses a static demo history and lets the AI
    compute the PFI, then augments the response with history.
    """
    history = {
        "freelancer_id": freelancer_id,
        "name": "Alex Johnson",
        "total_projects": 5,
        "milestones": [
            {"title": "Homepage Design", "verdict": "completed", "score": 92, "met_deadline": True},
            {"title": "Backend API", "verdict": "completed", "score": 88, "met_deadline": True},
            {"title": "Mobile UI", "verdict": "partial", "score": 65, "met_deadline": False},
            {"title": "Database Setup", "verdict": "completed", "score": 90, "met_deadline": True},
            {"title": "Final Testing", "verdict": "failed", "score": 30, "met_deadline": False},
            {"title": "Landing Page", "verdict": "completed", "score": 85, "met_deadline": True},
            {"title": "Payment Integration", "verdict": "completed", "score": 78, "met_deadline": True},
        ],
    }

    result = calculate_pfi(history)

    if not result["success"]:
        return {"error": result["error"]}

    data = result["data"]

    # Augment AI response so the frontend has full context
    data["name"] = history["name"]
    data["history"] = history["milestones"]
    data["total_projects"] = history["total_projects"]

    # Simple derived stats
    completed = len([m for m in history["milestones"] if m["verdict"] == "completed"])
    deadlines_met = len([m for m in history["milestones"] if m["met_deadline"]])
    data["completed"] = completed
    data["deadlines_met"] = deadlines_met

    return data


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)