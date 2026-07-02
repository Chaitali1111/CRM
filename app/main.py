from fastapi import FastAPI, Request, Form, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi import UploadFile, File
import os
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import engine, Base, get_db
from app.models import User, Lead, Campaign
from fastapi.responses import StreamingResponse
import csv
import io
from googlesearch import search
from app.google_maps import search_google_maps


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
     return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": "Invalid Email or Password"
        }
    )

    total_leads = db.query(Lead).count()
    total_campaigns = db.query(Campaign).count()
    total_groups = len(
    db.query(Lead.group_name)
    .filter(Lead.group_name != "")
    .distinct()
    .all()
)
    recent_leads = db.query(Lead).order_by(Lead.id.desc()).limit(5).all()

    return templates.TemplateResponse(
    "dashboard.html",
    {
        "request": request,
        "user": user,
        "total_leads": total_leads,
        "total_groups": total_groups,
        "recent_leads": recent_leads,
        "total_campaigns": total_campaigns
    }
)

@app.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    total_leads = db.query(Lead).count()
    total_campaigns = db.query(Campaign).count()
    
    total_groups = len(
    db.query(Lead.group_name)
    .filter(Lead.group_name != "")
    .distinct()
    .all()
)

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
            "total_groups": total_groups,
            "recent_leads": recent_leads,
            "total_campaigns": total_campaigns,
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
@app.get("/export-csv")
def export_csv(
    db: Session = Depends(get_db)
):

    leads = db.query(Lead).all()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Company",
        "Mobile",
        "Category",
        "Group",
        "City"
    ])

    for lead in leads:
        writer.writerow([
            lead.id,
            lead.company_name,
            lead.mobile_number,
            lead.category,
            lead.group_name,
            lead.city
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=leads.csv"
        }
    )

@app.post("/import-csv")
def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    try:
             contents = file.file.read().decode("utf-8")
    except:
            file.file.seek(0)
            contents = file.file.read().decode("latin-1")

    csv_reader = csv.DictReader(io.StringIO(contents))

    for row in csv_reader:

        new_lead = Lead(
            company_name=row.get("Company", ""),
            mobile_number=row.get("Mobile", ""),
            category=row.get("Category", ""),
            group_name=row.get("Group", ""),
            city=row.get("City", ""),
            address=""
        )

        db.add(new_lead)

    db.commit()

    return RedirectResponse(
        url="/leads",
        status_code=303
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


@app.get("/groups")
def view_groups(
    request: Request,
    search: str = "",
    db: Session = Depends(get_db)
):

    leads = db.query(Lead).all()

    group_data = {}

    for lead in leads:

        group = lead.group_name

        if group:

            if search and search.lower() not in group.lower():
                continue

            if group not in group_data:
                group_data[group] = 0

            group_data[group] += 1

    return templates.TemplateResponse(
        "groups.html",
        {
            "request": request,
            "group_data": group_data,
            "search": search
        }
    )

    leads = db.query(Lead).all()

    group_data = {}

    for lead in leads:
        group = lead.group_name

        if group:
            if group not in group_data:
                group_data[group] = 0

            group_data[group] += 1

    return templates.TemplateResponse(
        "groups.html",
        {
            "request": request,
            "group_data": group_data
        }
    )


@app.get("/group-leads/{group_name}")
def group_leads(
    group_name: str,
    request: Request,
    db: Session = Depends(get_db)
):

    leads = db.query(Lead).filter(
        Lead.group_name == group_name
    ).all()

    return templates.TemplateResponse(
        "group_leads.html",
        {
            "request": request,
            "group_name": group_name,
            "leads": leads
        }
    )


@app.get("/campaigns")
def campaigns(
    request: Request,
    db: Session = Depends(get_db)
):

    groups = db.query(Lead.group_name)\
        .distinct()\
        .filter(Lead.group_name != "")\
        .all()

    return templates.TemplateResponse(
        "campaigns.html",
        {
            "request": request,
            "groups": groups
        }
    )



@app.post("/save-campaign")
def save_campaign(
    campaign_name: str = Form(...),
    group_name: str = Form(...),
    message_content: str = Form(""),
    pdf_file: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    filename = ""

    if pdf_file and pdf_file.filename:

     os.makedirs("uploads", exist_ok=True)

     filename = pdf_file.filename

     file_path = os.path.join("uploads", filename)

     with open(file_path, "wb") as buffer:
        buffer.write(pdf_file.file.read())

    new_campaign = Campaign(
        campaign_name=campaign_name,
        group_name=group_name,
        message_content=message_content,
        pdf_file=filename
    )

    db.add(new_campaign)
    db.commit()

    return RedirectResponse(
        url="/campaigns",
        status_code=303
    )


@app.get("/campaign-list")
def campaign_list(
    request: Request,
    db: Session = Depends(get_db)
):

    campaigns = db.query(Campaign).all()

    return templates.TemplateResponse(
        "campaign_list.html",
        {
            "request": request,
            "campaigns": campaigns
        }
    )


@app.get("/view-pdf/{filename}")
def view_pdf(filename: str):

    file_path = os.path.join("uploads", filename)

    return FileResponse(
        path=file_path,
        media_type="application/pdf"

    )



@app.get("/google-test")
def google_test():

    results = []

    for url in search("Mobile Shop Mumbai", num_results=10):
        results.append(url)

    return {
        "results": results
    }


# ---------------- GOOGLE SEARCH PAGE ----------------

@app.get("/google-search")
def google_search_page(request: Request):
    return templates.TemplateResponse(
        "google_search.html",
        {"request": request}
    )


# ---------------- GOOGLE SEARCH ----------------

@app.post("/google-search")
def google_search(
    request: Request,
    keyword: str = Form(...),
    db: Session = Depends(get_db)
):

    results = search_google_maps(
        keyword,
        "",
        "",
        db
    )

    return templates.TemplateResponse(
        "google_search.html",
        {
            "request": request,
            "results": results,
            "keyword": keyword
        }
    )


@app.post("/save-google-lead")
def save_google_lead(
    company_name: str = Form(...),
    mobile_number: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    db: Session = Depends(get_db)
):

    existing = db.query(Lead).filter(
        Lead.company_name == company_name
    ).first()

    if not existing:

        lead = Lead(
            company_name=company_name,
            mobile_number=mobile_number,
            address=address,
            website=website,
            category="",
            group_name="",
            city=""
        )

        db.add(lead)
        db.commit()

    return RedirectResponse(
        url="/leads",
        status_code=303
    )