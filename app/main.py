from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import engine, Base, get_db
from app.models import User, Lead

Base.metadata.create_all(bind=engine)

app = FastAPI()

templates = Jinja2Templates(directory="templates")


# ---------------- LOGIN PAGE ----------------

@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.get("/login")
def login_redirect(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


# ---------------- REGISTER PAGE ----------------

@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


# ---------------- REGISTER USER ----------------

@app.post("/register")
def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):

    new_user = User(
        name=name,
        email=email,
        password=password,
        role=role
    )

    db.add(new_user)
    db.commit()

    return {
        "message": "User Registered Successfully"
    }


# ---------------- LOGIN USER ----------------

@app.post("/login")
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        and_(
            User.email == email,
            User.password == password
        )
    ).first()

    if not user:
        return {
            "message": "Invalid Email or Password"
        }

    total_leads = db.query(Lead).count()
    recent_leads = db.query(Lead).order_by(Lead.id.desc()).limit(5).all()

    return templates.TemplateResponse(
    "dashboard.html",
    {
        "request": request,
        "user": user,
        "total_leads": total_leads,
        "recent_leads": recent_leads
    }
)

@app.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    total_leads = db.query(Lead).count()

    recent_leads = db.query(Lead)\
        .order_by(Lead.id.desc())\
        .limit(5)\
        .all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": {
                "name": "Admin",
                "email": "admin@crm.com",
                "role": "Admin"
            },
            "total_leads": total_leads,
            "recent_leads": recent_leads
        }
    )
    


# ---------------- ADD LEAD PAGE ----------------

@app.get("/add-lead")
def add_lead_page(request: Request):
    return templates.TemplateResponse(
        "add_lead.html",
        {"request": request}
    )


# ---------------- SAVE LEAD ----------------

@app.post("/add-lead")
def save_lead(
    company_name: str = Form(...),
    mobile_number: str = Form(...),
    address: str = Form(""),
    category: str = Form(""),
    group_name: str = Form(""),
    city: str = Form(""),
    db: Session = Depends(get_db)
):

    new_lead = Lead(
        company_name=company_name,
        mobile_number=mobile_number,
        address=address,
        category=category,
        group_name=group_name,
        city=city
    )

    db.add(new_lead)
    db.commit()

    return RedirectResponse(
        url="/leads",
        status_code=303
    )


# ---------------- VIEW LEADS ----------------
@app.get("/leads")
def view_leads(
    request: Request,
    search: str = "",
    category: str = "",
    db: Session = Depends(get_db)
):

    query = db.query(Lead)

    if search:
        query = query.filter(
            Lead.company_name.ilike(f"%{search}%")
        )

    if category:
        query = query.filter(
            Lead.category == category
        )

    leads = query.all()

    return templates.TemplateResponse(
        "leads.html",
        {
            "request": request,
            "leads": leads,
            "search": search,
            "category": category
        }
    )

@app.get("/delete-lead/{lead_id}")
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db)
):

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    if lead:
        db.delete(lead)
        db.commit()

    return RedirectResponse(
        url="/leads",
        status_code=303
    )
@app.get("/edit-lead/{lead_id}")
def edit_lead_page(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    return templates.TemplateResponse(
        "edit_lead.html",
        {
            "request": request,
            "lead": lead
        }
    )
@app.get("/logout")
def logout():

    return RedirectResponse(
        url="/",
        status_code=303
    )
@app.get("/edit-lead/{lead_id}")
def edit_lead_page(
    lead_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    return templates.TemplateResponse(
        "edit_lead.html",
        {
            "request": request,
            "lead": lead
        }
    )

@app.post("/update-lead/{lead_id}")
def update_lead(
    lead_id: int,
    company_name: str = Form(...),
    mobile_number: str = Form(...),
    address: str = Form(""),
    category: str = Form(""),
    group_name: str = Form(""),
    city: str = Form(""),
    db: Session = Depends(get_db)
):

    lead = db.query(Lead).filter(
        Lead.id == lead_id
    ).first()

    lead.company_name = company_name
    lead.mobile_number = mobile_number
    lead.address = address
    lead.category = category
    lead.group_name = group_name
    lead.city = city

    db.commit()

    return RedirectResponse(
        url="/leads",
        status_code=303
    )


