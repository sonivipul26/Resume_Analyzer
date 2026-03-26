from pydantic import BaseModel, Field
from typing import List, Optional

class EvaluationResult(BaseModel):
    score: float = Field(description="Match Score (0-10) with 1 decimal precision. >= 7 is strong, 5-6 moderate, 0-4 poor.")
    result: str = Field(description="'PASS' if score >= 7, else 'FAIL'.")
    missing_keywords: List[str] = Field(description="List of keywords present in JD but missing in Resume.")
    skill_gaps: List[str] = Field(description="Specific skills the candidate lacks according to the JD.")
    weak_bullet_points: List[str] = Field(description="Identify any weak bullet points that lack impact or metrics.")
    ats_issues: List[str] = Field(description="Any structural/formatting issues that would fail an ATS system.")
    formatting_problems: List[str] = Field(description="General formatting advice.")
    suggestions: List[str] = Field(description="Detailed improvement suggestions and next steps.")

class OptimizedExperience(BaseModel):
    title: str
    company: str
    dates: str
    bullet_points: List[str] = Field(description="Action-oriented, metrics-driven bullet points aligning with the JD.")

class OptimizedEducation(BaseModel):
    degree: str
    institution: str
    dates: str

class OptimizedProject(BaseModel):
    name: str
    description: List[str] = Field(description="Action-oriented bullet points highlighting skills relevant to JD.")

class OptimizedResume(BaseModel):
    name: str = Field(description="Candidate's Full Name")
    contact_info: str = Field(description="Email, phone, LinkedIn, GitHub etc., separated by | or similar")
    summary: str = Field(description="A powerful 2-3 sentence professional summary tailored to the JD.")
    skills: List[str] = Field(description="List of relevant skills extracted and reasonably added based on JD compatibility.")
    experience: List[OptimizedExperience]
    education: List[OptimizedEducation]
    projects: List[OptimizedProject]
