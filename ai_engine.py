import os
from google import genai
from google.genai import types
from schemas import EvaluationResult, OptimizedResume

def get_client(api_key: str = None) -> genai.Client:
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)

def evaluate_resume(jd_text: str, resume_text: str, api_key: str = None) -> dict:
    """Evaluates the resume against the JD and returns a dictionary of insights."""
    client = get_client(api_key)
    
    prompt = f"""
You are an expert ATS (Applicant Tracking System) and Senior Technical Recruiter.
Evaluate the candidate's resume against the provided Job Description.

Job Description:
{jd_text}

Resume:
{resume_text}

Provide a blunt, detailed, and highly accurate analysis. Do not hallucinate. Be objective.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EvaluationResult,
                temperature=0.2
            ),
        )
        # response.text should be a JSON string that conforms to the schema.
        # We can parse it using Pydantic
        import json
        result_dict = json.loads(response.text)
        return result_dict
    except Exception as e:
        print(f"Error evaluating resume: {e}")
        return {
            "score": 0.0,
            "result": "FAIL",
            "error": str(e)
        }

def optimize_resume(jd_text: str, resume_text: str, api_key: str = None) -> dict:
    """Rewrites and optimizes the resume structurally to match the JD."""
    client = get_client(api_key)
    
    prompt = f"""
You are a world-class Resume Writer. Your task is to rewrite and optimize the following candidate's resume to strictly align with the provided Job Description.
Do NOT fabricate false experience. Only rephrase, add relevant action verbs, highlight relevant overlapping skills, and improve the bullet points to be ATS friendly and impactful.
If the candidate has relevant skills implied by their experience, you may add them to the skills list.

Return ONLY a perfectly formatted JSON object that matches exactly this structure:
{{
    "name": "Author Full Name",
    "contact_info": "Email | Phone | LinkedIn etc.",
    "summary": "Professional summary...",
    "skills": ["Skill1", "Skill2"],
    "experience": [
        {{
            "title": "Role",
            "company": "Company Name",
            "dates": "2020 - 2022",
            "bullet_points": ["Point 1", "Point 2"]
        }}
    ],
    "education": [
        {{
            "degree": "Degree",
            "institution": "University",
            "dates": "2016 - 2020"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": ["Point 1", "Point 2"]
        }}
    ]
}}

Job Description:
{jd_text}

Original Resume:
{resume_text}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4
            ),
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"Error optimizing resume: {e}")
        return {"error": str(e)}
