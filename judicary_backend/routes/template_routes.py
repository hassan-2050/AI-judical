"""
Template Routes – Legal document templates CRUD API.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from models.template_model import Template
from routes.auth_routes import token_required, admin_required

logger = logging.getLogger(__name__)

template_bp = Blueprint("templates", __name__)

# ----- Seed default templates on first request -----

_templates_seeded = False


def seed_templates():
    """Create default legal templates if none exist."""
    global _templates_seeded
    if _templates_seeded:
        return
    _templates_seeded = True

    if Template.objects.count() > 0:
        return

    defaults = [
        {
            "name": "Bail Application",
            "description": "Standard bail application format for criminal cases",
            "category": "bail_application",
            "language": "en",
            "court_type": "Session Court",
            "content": """IN THE COURT OF {{court_name}}

BAIL APPLICATION NO. _____ OF {{year}}

{{applicant_name}} (Applicant)
versus
The State (Respondent)

FIR No. {{fir_number}}
Police Station: {{police_station}}
Under Section: {{sections}}

PETITION FOR BAIL

Respectfully Sheweth:

1. That the applicant {{applicant_name}} S/O {{father_name}}, aged {{age}} years, R/O {{address}} has been arrested on {{arrest_date}} in the above-mentioned FIR.

2. That the applicant is innocent and has been falsely implicated in this case.

3. That the investigation has been completed and the applicant is no longer required for investigation purposes.

4. That the applicant is a respectable citizen with no prior criminal record.

5. That the applicant undertakes to appear before this Honourable Court on each and every date of hearing.

PRAYER:
It is therefore most respectfully prayed that the applicant may kindly be granted bail in the above-mentioned case in the interest of justice.

Dated: {{date}}

{{advocate_name}}
Advocate for Applicant""",
            "placeholders": ["court_name", "year", "applicant_name", "father_name", "age", "address", "arrest_date", "fir_number", "police_station", "sections", "date", "advocate_name"],
        },
        {
            "name": "Writ Petition",
            "description": "Constitutional writ petition under Article 199",
            "category": "writ_petition",
            "language": "en",
            "court_type": "High Court",
            "content": """IN THE {{court_name}}
{{bench_location}}

WRIT PETITION NO. _____ OF {{year}}

{{petitioner_name}} (Petitioner)
versus
{{respondent_name}} (Respondent)

CONSTITUTIONAL PETITION UNDER ARTICLE 199 OF THE CONSTITUTION OF PAKISTAN, 1973

Respectfully Sheweth:

1. BRIEF FACTS:
{{brief_facts}}

2. GROUNDS:
(a) That the impugned action/order is without lawful authority and jurisdiction.
(b) That the impugned action/order is violative of the fundamental rights of the petitioner guaranteed under Articles {{articles}} of the Constitution.
(c) {{additional_grounds}}

3. That no other adequate remedy is available to the petitioner.

PRAYER:
It is most respectfully prayed that this Honourable Court may graciously be pleased to:
(a) Accept this Writ Petition;
(b) Set aside the impugned order/action dated {{impugned_date}};
(c) Grant any other relief deemed fit by this Honourable Court.

Dated: {{date}}

{{advocate_name}}
Advocate for Petitioner""",
            "placeholders": ["court_name", "bench_location", "year", "petitioner_name", "respondent_name", "brief_facts", "articles", "additional_grounds", "impugned_date", "date", "advocate_name"],
        },
        {
            "name": "Legal Notice",
            "description": "Standard legal notice format",
            "category": "legal_notice",
            "language": "en",
            "content": """LEGAL NOTICE

Date: {{date}}

To:
{{recipient_name}}
{{recipient_address}}

From:
{{sender_name}} (through {{advocate_name}}, Advocate)

Subject: Legal Notice under {{relevant_law}}

Sir/Madam,

Under instructions from and on behalf of my client {{sender_name}}, I address this legal notice to you as under:

1. {{fact_1}}

2. {{fact_2}}

3. {{fact_3}}

That you are hereby called upon to {{demand}} within {{time_period}} days of the receipt of this notice, failing which my client shall be constrained to initiate legal proceedings against you before the competent court of law, at your risk, cost and consequences.

This notice is being sent to you without prejudice to the rights and remedies of my client.

{{advocate_name}}
Advocate High Court
{{advocate_address}}
{{advocate_phone}}""",
            "placeholders": ["date", "recipient_name", "recipient_address", "sender_name", "advocate_name", "relevant_law", "fact_1", "fact_2", "fact_3", "demand", "time_period", "advocate_address", "advocate_phone"],
        },
        {
            "name": "Power of Attorney",
            "description": "General power of attorney format",
            "category": "power_of_attorney",
            "language": "en",
            "content": """GENERAL POWER OF ATTORNEY

KNOW ALL MEN BY THESE PRESENTS:

I, {{principal_name}}, S/D/W of {{father_husband_name}}, CNIC No. {{cnic}}, resident of {{address}} (hereinafter referred to as the "Principal") do hereby appoint, nominate, constitute and authorize:

{{attorney_name}}, S/D/W of {{attorney_father}}, CNIC No. {{attorney_cnic}}, resident of {{attorney_address}} (hereinafter referred to as the "Attorney")

as my true and lawful Attorney to act on my behalf with full power and authority to:

1. {{power_1}}
2. {{power_2}}
3. {{power_3}}

And I do hereby agree and declare that all acts, deeds and things done by the said Attorney shall be deemed as done by me.

This Power of Attorney shall remain in force until revoked by me in writing.

IN WITNESS WHEREOF, I have set my hand on this {{date}}.

_____________________
{{principal_name}} (Principal)

WITNESSES:
1. Name: ___________ CNIC: ___________
2. Name: ___________ CNIC: ___________""",
            "placeholders": ["principal_name", "father_husband_name", "cnic", "address", "attorney_name", "attorney_father", "attorney_cnic", "attorney_address", "power_1", "power_2", "power_3", "date"],
        },
        {
            "name": "Affidavit",
            "description": "Standard affidavit format on stamp paper",
            "category": "affidavit",
            "language": "en",
            "content": """AFFIDAVIT

I, {{deponent_name}}, S/D/W of {{father_husband_name}}, aged {{age}} years, CNIC No. {{cnic}}, resident of {{address}}, do hereby solemnly affirm and state on oath as under:

1. That I am the deponent herein and am competent to swear this affidavit.

2. {{statement_1}}

3. {{statement_2}}

4. {{statement_3}}

5. That the contents of this affidavit are true and correct to the best of my knowledge and belief.

DEPONENT

VERIFICATION:
Verified at {{city}} on this {{date}} that the contents of the above affidavit are true and correct to the best of my knowledge and belief and nothing has been concealed therein.

DEPONENT""",
            "placeholders": ["deponent_name", "father_husband_name", "age", "cnic", "address", "statement_1", "statement_2", "statement_3", "city", "date"],
        },
        {
            "name": "ضمانت کی درخواست",
            "description": "اردو میں ضمانت کی درخواست کا معیاری فارمیٹ",
            "category": "bail_application",
            "language": "ur",
            "court_type": "سیشن کورٹ",
            "content": """بعدالت {{عدالت_کا_نام}}

ضمانت کی درخواست نمبر _____ بابت {{سال}}

{{درخواست_گزار_کا_نام}} (درخواست گزار)
بنام
ریاست (مجیب)

ایف آئی آر نمبر: {{ایف_آئی_آر_نمبر}}
تھانہ: {{تھانہ}}
بموجب دفعات: {{دفعات}}

ضمانت کی درخواست

بعد ادب گزارش ہے:

1. کہ درخواست گزار {{درخواست_گزار_کا_نام}} ولد {{والد_کا_نام}} عمر {{عمر}} سال ساکن {{پتہ}} کو مذکورہ بالا ایف آئی آر میں بتاریخ {{گرفتاری_کی_تاریخ}} گرفتار کیا گیا۔

2. کہ درخواست گزار بے قصور ہے اور اسے جھوٹا پھنسایا گیا ہے۔

3. کہ تفتیش مکمل ہو چکی ہے اور درخواست گزار کی مزید ضرورت نہیں ہے۔

التجا:
لہذا عدالت عالیہ سے التجا ہے کہ درخواست گزار کو مذکورہ مقدمے میں ضمانت عطا فرمائی جائے۔

مؤرخہ: {{تاریخ}}

{{وکیل_کا_نام}}
ایڈووکیٹ برائے درخواست گزار""",
            "placeholders": ["عدالت_کا_نام", "سال", "درخواست_گزار_کا_نام", "والد_کا_نام", "عمر", "پتہ", "گرفتاری_کی_تاریخ", "ایف_آئی_آر_نمبر", "تھانہ", "دفعات", "تاریخ", "وکیل_کا_نام"],
        },
    ]

    for tpl_data in defaults:
        try:
            tpl = Template(**tpl_data)
            tpl.save()
            logger.info("Seeded template: %s", tpl_data["name"])
        except Exception as e:
            logger.error("Failed to seed template %s: %s", tpl_data["name"], e)


@template_bp.route("/templates", methods=["GET"])
def list_templates():
    """List all available legal templates."""
    seed_templates()

    category = request.args.get("category")
    language = request.args.get("language")

    query = Template.objects(is_active=True)
    if category:
        query = query.filter(category=category)
    if language:
        query = query.filter(language=language)

    templates = query.order_by("category", "name")
    return jsonify({
        "templates": [t.to_card() for t in templates],
        "total": templates.count(),
    }), 200


@template_bp.route("/templates/<template_id>", methods=["GET"])
def get_template(template_id):
    """Get a specific template with full content."""
    seed_templates()
    try:
        tpl = Template.objects(id=template_id).first()
    except Exception:
        return jsonify({"error": "Invalid template ID"}), 400

    if not tpl:
        return jsonify({"error": "Template not found"}), 404

    # Increment usage count
    tpl.usage_count += 1
    tpl.save()

    return jsonify({"template": tpl.to_json()}), 200


@template_bp.route("/templates", methods=["POST"])
@token_required
def create_template():
    """Create a new legal template (auth required)."""
    data = request.json or {}
    required = ["name", "category", "content"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    tpl = Template(
        name=data["name"],
        description=data.get("description", ""),
        category=data["category"],
        language=data.get("language", "en"),
        content=data["content"],
        placeholders=data.get("placeholders", []),
        court_type=data.get("court_type"),
        jurisdiction=data.get("jurisdiction"),
        created_by=g.current_user.id,
    )
    tpl.save()

    return jsonify({
        "message": "Template created",
        "template": tpl.to_json(),
    }), 201


@template_bp.route("/templates/<template_id>/generate", methods=["POST"])
def generate_document(template_id):
    """Generate a document from a template by filling placeholders."""
    try:
        tpl = Template.objects(id=template_id).first()
    except Exception:
        return jsonify({"error": "Invalid template ID"}), 400

    if not tpl:
        return jsonify({"error": "Template not found"}), 404

    data = request.json or {}
    values = data.get("values", {})

    content = tpl.content
    for placeholder, value in values.items():
        content = content.replace("{{" + placeholder + "}}", str(value))

    # Check for unfilled placeholders
    import re
    unfilled = re.findall(r'\{\{(\w+)\}\}', content)

    return jsonify({
        "document": content,
        "template_name": tpl.name,
        "unfilled_placeholders": unfilled,
    }), 200


@template_bp.route("/templates/categories", methods=["GET"])
def list_categories():
    """List all template categories."""
    categories = [
        {"value": "petition", "label": "Petition"},
        {"value": "affidavit", "label": "Affidavit"},
        {"value": "contract", "label": "Contract"},
        {"value": "legal_notice", "label": "Legal Notice"},
        {"value": "power_of_attorney", "label": "Power of Attorney"},
        {"value": "bail_application", "label": "Bail Application"},
        {"value": "writ_petition", "label": "Writ Petition"},
        {"value": "appeal", "label": "Appeal"},
        {"value": "complaint", "label": "Complaint"},
        {"value": "agreement", "label": "Agreement"},
        {"value": "other", "label": "Other"},
    ]
    return jsonify({"categories": categories}), 200
