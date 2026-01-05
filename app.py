import streamlit as st
def set_sidebar_style():
    import streamlit as st
    st.markdown(
        """
        <style>
        /* Premium dark interactive style for ONLY first 3 buttons */
        section[data-testid="stSidebar"] .stButton:nth-of-type(-n+3) button {
            background: linear-gradient(135deg, #0f172a, #1e293b) !important;
            color: #e5e7eb !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 0.3s ease;
        }

        /* Hover: subtle lift + glow */
        section[data-testid="stSidebar"] .stButton:nth-of-type(-n+3) button:hover {
            background: linear-gradient(135deg, #020617, #0f172a) !important;
            color: #ffffff !important;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.55);
            transform: translateY(-2px);
        }

        /* Active: solid focus (best UX) */
        section[data-testid="stSidebar"] .stButton:nth-of-type(-n+3) button:focus {
            background: #020617 !important;
            color: #ffffff !important;
            border: 1px solid #38bdf8 !important;
            box-shadow: 0 0 14px rgba(56, 189, 248, 0.45);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def section_header(title, subtitle=""):
    import streamlit as st
    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #005C97, #363795); 
                    padding: 1.2rem; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">{title}</h2>
            <p style="color: #d9e4f5; margin: 0;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

def feature_card(title, description, icon, target_page):
    import streamlit as st
    st.markdown(
        f"<div style='text-align:center; font-size:30px; margin-bottom:10px;'><i class='{icon}'></i></div>",
        unsafe_allow_html=True
    )
    if st.button(title, use_container_width=True, key=title):
        st.session_state.page = target_page
        st.rerun()
    st.caption(description)

st.set_page_config(
    page_title="AI Powered Resume Maker and Ranker",
    page_icon="🚀",
    layout="wide"
)

import json
import pandas as pd
import plotly.express as px
import traceback
from utils.resume_analyzer import ResumeAnalyzer
from utils.resume_builder import ResumeBuilder
from config.database import (
    get_database_connection, save_resume_data, save_analysis_data, 
    init_database, verify_admin, log_admin_action
)
from config.job_roles import JOB_ROLES
from config.courses import COURSES_BY_CATEGORY, RESUME_VIDEOS, INTERVIEW_VIDEOS, get_courses_for_role, get_category_for_role
import requests
from streamlit_lottie import st_lottie
import plotly.graph_objects as go
import base64
import io
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from ui_components import (
    apply_modern_styles, hero_section, page_header
)
from datetime import datetime
from PIL import Image

class ResumeApp:
    def __init__(self):
        """Initialize the application"""
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {
                'personal_info': {
                    'full_name': '',
                    'email': '',
                    'phone': '',
                    'location': '',
                    'linkedin': '',
                    'portfolio': ''
                },
                'summary': '',
                'experiences': [],
                'education': [],
                'projects': [],
                'skills_categories': {
                    'technical': [],
                    'soft': [],
                    'languages': [],
                    'tools': []
                }
            }
        
        if 'page' not in st.session_state:
            st.session_state.page = 'home'
            
        if 'is_admin' not in st.session_state:
            st.session_state.is_admin = False
        
        self.pages = {
            "🏠 HOME": self.render_home,
            "🔍 RESUME ANALYZER": self.render_analyzer,
            "📝 RESUME BUILDER": self.render_builder,
        }

        self.job_roles = JOB_ROLES
        self.analyzer = ResumeAnalyzer()
        self.builder = ResumeBuilder()

    def load_lottie_url(self, url: str):
        """Load Lottie animation from URL safely with error handling"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️ Failed to load Lottie animation from {url}: {e}")
            return None

    def apply_global_styles(self):
        st.markdown("""
        <style>
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #1a1a1a;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: #4CAF50;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #45a049;
        }

        /* Global Styles */
        .main-header {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .main-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.1) 100%);
            z-index: 1;
        }

        .main-header h1 {
            color: white;
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }

        /* Template Card Styles */
        .template-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 2rem;
            padding: 1rem;
        }

        .template-card {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .template-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            border-color: #4CAF50;
        }

        .template-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 0%, rgba(76,175,80,0.1) 100%);
            z-index: 1;
        }

        .template-icon {
            font-size: 3rem;
            color: #4CAF50;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }

        .template-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1rem;
            position: relative;
            z-index: 2;
        }

        .template-description {
            color: #aaa;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
            line-height: 1.6;
        }

        /* Feature List Styles */
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 1.5rem 0;
            position: relative;
            z-index: 2;
        }

        .feature-item {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            color: #ddd;
            font-size: 0.95rem;
        }

        .feature-icon {
            color: #4CAF50;
            margin-right: 0.8rem;
            font-size: 1.1rem;
        }

        /* Button Styles */
        .action-button {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-weight: 500;
            cursor: pointer;
            width: 100%;
            text-align: center;
            position: relative;
            overflow: hidden;
            z-index: 2;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(76,175,80,0.3);
        }

        .action-button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%);
            transition: all 0.6s ease;
        }

        .action-button:hover::before {
            left: 100%;
        }

        /* Form Section Styles */
        .form-section {
            background: rgba(45, 45, 45, 0.9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .form-section-title {
            font-size: 1.8rem;
            font-weight: 600;
            color: white;
            margin-bottom: 1.5rem;
            padding-bottom: 0.8rem;
            border-bottom: 2px solid #4CAF50;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-label {
            color: #ddd;
            font-weight: 500;
            margin-bottom: 0.8rem;
            display: block;
        }

        .form-input {
            width: 100%;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
            background: rgba(30, 30, 30, 0.9);
            color: white;
            transition: all 0.3s ease;
        }

        .form-input:focus {
            border-color: #4CAF50;
            box-shadow: 0 0 0 2px rgba(76,175,80,0.2);
            outline: none;
        }

        /* Skill Tags */
        .skill-tag-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.8rem;
            margin-top: 1rem;
        }

        .skill-tag {
            background: rgba(76,175,80,0.1);
            color: #4CAF50;
            padding: 0.6rem 1.2rem;
            border-radius: 50px;
            border: 1px solid #4CAF50;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .skill-tag:hover {
            background: #4CAF50;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(76,175,80,0.2);
        }

        /* Progress Circle */
        .progress-container {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 2rem auto;
        }

        .progress-circle {
            transform: rotate(-90deg);
            width: 100%;
            height: 100%;
        }

        .progress-circle circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
            stroke: #4CAF50;
            transform-origin: 50% 50%;
            transition: all 0.3s ease;
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.5rem;
            font-weight: 600;
            color: white;
        }

        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .animate-slide-in {
            animation: slideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .template-container {
                grid-template-columns: 1fr;
            }

            .main-header {
                padding: 1.5rem;
            }

            .main-header h1 {
                font-size: 2rem;
            }

            .template-card {
                padding: 1.5rem;
            }

            .action-button {
                padding: 0.8rem 1.6rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)

    def load_image(self, image_name):
        """Load image from static directory"""
        try:
            image_path = f"c:/Users/shree/Downloads/smart-resume-ai/{image_name}"
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            encoded = base64.b64encode(image_bytes).decode()
            return f"data:image/png;base64,{encoded}"
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
            return None

    def export_to_excel(self):
        """Export resume data to Excel"""
        conn = get_database_connection()
        
        query = """
            SELECT 
                rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
                rd.summary, rd.target_role, rd.target_category,
                rd.education, rd.experience, rd.projects, rd.skills,
                ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
                ra.missing_skills, ra.recommendations,
                rd.created_at
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
        """
        
        try:
            df = pd.read_sql_query(query, conn)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Resume Data')
            
            return output.getvalue()
        except Exception as e:
            print(f"Error exporting to Excel: {str(e)}")
            return None
        finally:
            conn.close()


    def render_empty_state(self, icon, message):
        """Render an empty state with icon and message"""
        return f"""
            <div style='text-align: center; padding: 2rem; color: #666;'>
                <i class='{icon}' style='font-size: 2rem; margin-bottom: 1rem; color: #00bfa5;'></i>
                <p style='margin: 0;'>{message}</p>
            </div>
        """

    def analyze_resume(self, resume_text):
        """Analyze resume and store results"""
        analytics = self.analyzer.analyze_resume(resume_text)
        st.session_state.analytics_data = analytics
        return analytics

    def handle_resume_upload(self):
        """Handle resume upload and analysis"""
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file)
                else:
                    resume_text = extract_text_from_docx(uploaded_file)
                
                st.session_state.resume_data = {
                    'filename': uploaded_file.name,
                    'content': resume_text,
                    'upload_time': datetime.now().isoformat()
                }
                
                analytics = self.analyze_resume(resume_text)
                
                return True
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")
                return False
        return False

    def render_builder(self):
        section_header("Resume Builder",
                       "Create ATS-friendly professional resumes with ease.")
        
        template_options = ["Modern", "Professional", "Minimal", "Creative"]
        selected_template = st.selectbox("Select Resume Template", template_options)
        st.success(f"🎨 Currently using: {selected_template} Template")

        st.subheader("Personal Information")
        
        col1, col2 = st.columns(2)
        with col1:
            existing_name = st.session_state.form_data['personal_info']['full_name']
            existing_email = st.session_state.form_data['personal_info']['email']
            existing_phone = st.session_state.form_data['personal_info']['phone']
            
            full_name = st.text_input("Full Name", value=existing_name)
            email = st.text_input("Email", value=existing_email, key="email_input")
            phone = st.text_input("Phone", value=existing_phone)

            if 'email_input' in st.session_state:
                st.session_state.form_data['personal_info']['email'] = st.session_state.email_input
        
        with col2:
            existing_location = st.session_state.form_data['personal_info']['location']
            existing_linkedin = st.session_state.form_data['personal_info']['linkedin']
            existing_portfolio = st.session_state.form_data['personal_info']['portfolio']
            
            location = st.text_input("Location", value=existing_location)
            linkedin = st.text_input("LinkedIn URL", value=existing_linkedin)
            portfolio = st.text_input("Portfolio Website", value=existing_portfolio)

        st.session_state.form_data['personal_info'] = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'location': location,
            'linkedin': linkedin,
            'portfolio': portfolio
        }

        st.subheader("Professional Summary")
        summary = st.text_area("Professional Summary", value=st.session_state.form_data.get('summary', ''), height=150,
                             help="Write a brief summary highlighting your key skills and experience")
        
        st.subheader("Work Experience")
        if 'experiences' not in st.session_state.form_data:
            st.session_state.form_data['experiences'] = []
            
        if st.button("Add Experience"):
            st.session_state.form_data['experiences'].append({
                'company': '',
                'position': '',
                'start_date': '',
                'end_date': '',
                'description': '',
                'responsibilities': [],
                'achievements': []
            })
        
        for idx, exp in enumerate(st.session_state.form_data['experiences']):
            with st.expander(f"Experience {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    exp['company'] = st.text_input("Company Name", key=f"company_{idx}", value=exp.get('company', ''))
                    exp['position'] = st.text_input("Position", key=f"position_{idx}", value=exp.get('position', ''))
                with col2:
                    exp['start_date'] = st.text_input("Start Date", key=f"start_date_{idx}", value=exp.get('start_date', ''))
                    exp['end_date'] = st.text_input("End Date", key=f"end_date_{idx}", value=exp.get('end_date', ''))
                
                exp['description'] = st.text_area("Role Overview", key=f"desc_{idx}", 
                                                value=exp.get('description', ''),
                                                help="Brief overview of your role and impact")
                
                st.markdown("##### Key Responsibilities")
                resp_text = st.text_area("Enter responsibilities (one per line)", 
                                       key=f"resp_{idx}",
                                       value='\n'.join(exp.get('responsibilities', [])),
                                       height=100,
                                       help="List your main responsibilities, one per line")
                exp['responsibilities'] = [r.strip() for r in resp_text.split('\n') if r.strip()]
                
                st.markdown("##### Key Achievements")
                achv_text = st.text_area("Enter achievements (one per line)", 
                                       key=f"achv_{idx}",
                                       value='\n'.join(exp.get('achievements', [])),
                                       height=100,
                                       help="List your notable achievements, one per line")
                exp['achievements'] = [a.strip() for a in achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Experience", key=f"remove_exp_{idx}"):
                    st.session_state.form_data['experiences'].pop(idx)
                    st.rerun()
        
        st.subheader("Projects")
        if 'projects' not in st.session_state.form_data:
            st.session_state.form_data['projects'] = []
            
        if st.button("Add Project"):
            st.session_state.form_data['projects'].append({
                'name': '',
                'technologies': '',
                'description': '',
                'responsibilities': [],
                'achievements': [],
                'link': ''
            })
        
        for idx, proj in enumerate(st.session_state.form_data['projects']):
            with st.expander(f"Project {idx + 1}", expanded=True):
                proj['name'] = st.text_input("Project Name", key=f"proj_name_{idx}", value=proj.get('name', ''))
                proj['technologies'] = st.text_input("Technologies Used", key=f"proj_tech_{idx}", 
                                                   value=proj.get('technologies', ''),
                                                   help="List the main technologies, frameworks, and tools used")
                
                proj['description'] = st.text_area("Project Overview", key=f"proj_desc_{idx}", 
                                                 value=proj.get('description', ''),
                                                 help="Brief overview of the project and its goals")
                
                st.markdown("##### Key Responsibilities")
                proj_resp_text = st.text_area("Enter responsibilities (one per line)", 
                                            key=f"proj_resp_{idx}",
                                            value='\n'.join(proj.get('responsibilities', [])),
                                            height=100,
                                            help="List your main responsibilities in the project")
                proj['responsibilities'] = [r.strip() for r in proj_resp_text.split('\n') if r.strip()]
                
                st.markdown("##### Key Achievements")
                proj_achv_text = st.text_area("Enter achievements (one per line)", 
                                            key=f"proj_achv_{idx}",
                                            value='\n'.join(proj.get('achievements', [])),
                                            height=100,
                                            help="List the project's key achievements and your contributions")
                proj['achievements'] = [a.strip() for a in proj_achv_text.split('\n') if a.strip()]
                
                proj['link'] = st.text_input("Project Link (optional)", key=f"proj_link_{idx}", 
                                           value=proj.get('link', ''),
                                           help="Link to the project repository, demo, or documentation")
                
                if st.button("Remove Project", key=f"remove_proj_{idx}"):
                    st.session_state.form_data['projects'].pop(idx)
                    st.rerun()
        
        st.subheader("Education")
        if 'education' not in st.session_state.form_data:
            st.session_state.form_data['education'] = []
            
        if st.button("Add Education"):
            st.session_state.form_data['education'].append({
                'school': '',
                'degree': '',
                'field': '',
                'graduation_date': '',
                'gpa': '',
                'achievements': []
            })
        
        for idx, edu in enumerate(st.session_state.form_data['education']):
            with st.expander(f"Education {idx + 1}", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    edu['school'] = st.text_input("School/University", key=f"school_{idx}", value=edu.get('school', ''))
                    edu['degree'] = st.text_input("Degree", key=f"degree_{idx}", value=edu.get('degree', ''))
                with col2:
                    edu['field'] = st.text_input("Field of Study", key=f"field_{idx}", value=edu.get('field', ''))
                    edu['graduation_date'] = st.text_input("Graduation Date", key=f"grad_date_{idx}", 
                                                         value=edu.get('graduation_date', ''))
                
                edu['gpa'] = st.text_input("GPA (optional)", key=f"gpa_{idx}", value=edu.get('gpa', ''))
                
                st.markdown("##### Achievements & Activities")
                edu_achv_text = st.text_area("Enter achievements (one per line)", 
                                           key=f"edu_achv_{idx}",
                                           value='\n'.join(edu.get('achievements', [])),
                                           height=100,
                                           help="List academic achievements, relevant coursework, or activities")
                edu['achievements'] = [a.strip() for a in edu_achv_text.split('\n') if a.strip()]
                
                if st.button("Remove Education", key=f"remove_edu_{idx}"):
                    st.session_state.form_data['education'].pop(idx)
                    st.rerun()
        
        st.subheader("Skills")
        if 'skills_categories' not in st.session_state.form_data:
            st.session_state.form_data['skills_categories'] = {
                'technical': [],
                'soft': [],
                'languages': [],
                'tools': []
            }
        
        col1, col2 = st.columns(2)
        with col1:
            tech_skills = st.text_area("Technical Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['technical']),
                                     height=150,
                                     help="Programming languages, frameworks, databases, etc.")
            st.session_state.form_data['skills_categories']['technical'] = [s.strip() for s in tech_skills.split('\n') if s.strip()]
            
            soft_skills = st.text_area("Soft Skills (one per line)", 
                                     value='\n'.join(st.session_state.form_data['skills_categories']['soft']),
                                     height=150,
                                     help="Leadership, communication, problem-solving, etc.")
            st.session_state.form_data['skills_categories']['soft'] = [s.strip() for s in soft_skills.split('\n') if s.strip()]
        
        with col2:
            languages = st.text_area("Languages (one per line)", 
                                   value='\n'.join(st.session_state.form_data['skills_categories']['languages']),
                                   height=150,
                                   help="Programming or human languages with proficiency level")
            st.session_state.form_data['skills_categories']['languages'] = [l.strip() for l in languages.split('\n') if l.strip()]
            
            tools = st.text_area("Tools & Technologies (one per line)", 
                               value='\n'.join(st.session_state.form_data['skills_categories']['tools']),
                               height=150,
                               help="Development tools, software, platforms, etc.")
            st.session_state.form_data['skills_categories']['tools'] = [t.strip() for t in tools.split('\n') if t.strip()]
        
        st.session_state.form_data.update({
            'summary': summary
        })
        
        if st.button("Generate Resume 📄", type="primary"):
            print("Validating form data...")
            print(f"Session state form data: {st.session_state.form_data}")
            print(f"Email input value: {st.session_state.get('email_input', '')}")
            
            current_name = st.session_state.form_data['personal_info']['full_name'].strip()
            current_email = st.session_state.email_input if 'email_input' in st.session_state else ''
            
            print(f"Current name: {current_name}")
            print(f"Current email: {current_email}")
            
            if not current_name:
                st.error("⚠️ Please enter your full name.")
                return
            
            if not current_email:
                st.error("⚠️ Please enter your email address.")
                return
                
            st.session_state.form_data['personal_info']['email'] = current_email
            
            try:
                print("Preparing resume data...")
                resume_data = {
                    "personal_info": st.session_state.form_data['personal_info'],
                    "summary": st.session_state.form_data.get('summary', '').strip(),
                    "experience": st.session_state.form_data.get('experiences', []),
                    "education": st.session_state.form_data.get('education', []),
                    "projects": st.session_state.form_data.get('projects', []),
                    "skills": st.session_state.form_data.get('skills_categories', {
                        'technical': [],
                        'soft': [],
                        'languages': [],
                        'tools': []
                    }),
                    "template": selected_template
                }
                
                print(f"Resume data prepared: {resume_data}")
                
                try:
                    resume_buffer = self.builder.generate_resume(resume_data)
                    if resume_buffer:
                        try:
                            save_resume_data(resume_data)
                            
                            st.success("✅ Resume generated successfully!")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                        except Exception as db_error:
                            print(f"Warning: Failed to save to database: {str(db_error)}")
                            st.warning("⚠️ Resume generated but couldn't be saved to database")
                            st.download_button(
                                label="Download Resume 📥",
                                data=resume_buffer,
                                file_name=f"{current_name.replace(' ', '_')}_resume.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    else:
                        st.error("❌ Failed to generate resume. Please try again.")
                        print("Resume buffer was None")
                except Exception as gen_error:
                    print(f"Error during resume generation: {str(gen_error)}")
                    print(f"Full traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error generating resume: {str(gen_error)}")
                        
            except Exception as e:
                print(f"Error preparing resume data: {str(e)}")
                print(f"Full traceback: {traceback.format_exc()}")
                st.error(f"❌ Error preparing resume data: {str(e)}")
        st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>© Aastha</p>", unsafe_allow_html=True)
    
    
    def render_analyzer(self):
        """Render the resume analyzer page"""
        apply_modern_styles()
        
        section_header("Resume Analyzer",
                       "Upload your resume and get instant feedback on skills and improvements.")
        
        categories = list(self.job_roles.keys())
        selected_category = st.selectbox("Job Category", categories)
        
        roles = self.job_roles[selected_category]
        selected_role = st.selectbox("Specific Role", roles)
        
        role_info = self.job_roles[selected_category][selected_role]
        
        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0;'>
            <h3>{selected_role}</h3>
            <p>{role_info['description']}</p>
            <h4>Required Skills:</h4>
            <p>{', '.join(role_info['required_skills'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload your resume", type=['pdf', 'docx'])
        
        st.markdown(
            self.render_empty_state(
            "fas fa-cloud-upload-alt",
            "Upload your resume to get started with AI-powered analysis"
            ),
            unsafe_allow_html=True
        )
        if uploaded_file:
            with st.spinner("Analyzing your document..."):
                text = ""
                try:
                    if uploaded_file.type == "application/pdf":
                        text = self.analyzer.extract_text_from_pdf(uploaded_file)
                    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        text = self.analyzer.extract_text_from_docx(uploaded_file)
                    else:
                        text = uploaded_file.getvalue().decode()
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    return

                
                analysis = self.analyzer.analyze_resume({'raw_text': text}, role_info)
                
                resume_data = {
                    'personal_info': {
                        'name': analysis.get('name', ''),
                        'email': analysis.get('email', ''),
                        'phone': analysis.get('phone', ''),
                        'linkedin': analysis.get('linkedin', ''),
                        'github': analysis.get('github', ''),
                        'portfolio': analysis.get('portfolio', '')
                    },
                    'summary': analysis.get('summary', ''),
                    'target_role': selected_role,
                    'target_category': selected_category,
                    'education': analysis.get('education', []),
                    'experience': analysis.get('experience', []),
                    'projects': analysis.get('projects', []),
                    'skills': analysis.get('skills', []),
                    'template': ''
                }
                
                try:
                    resume_id = save_resume_data(resume_data)
                    
                    analysis_data = {
                        'resume_id': resume_id,
                        'ats_score': analysis['ats_score'],
                        'keyword_match_score': analysis['keyword_match']['score'],
                        'format_score': analysis['format_score'],
                        'section_score': analysis['section_score'],
                        'missing_skills': ','.join(analysis['keyword_match']['missing_skills']),
                        'recommendations': ','.join(analysis['suggestions'])
                    }
                    save_analysis_data(resume_id, analysis_data)
                    st.success("Resume data saved successfully!")
                except Exception as e:
                    st.error(f"Error saving to database: {str(e)}")
                    print(f"Database error: {e}")
                
                if analysis.get('document_type') != 'resume':
                    st.error(f"⚠️ This appears to be a {analysis['document_type']} document, not a resume!")
                    st.warning("Please upload a proper resume for ATS analysis.")
                    return                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="feature-card">
                        <h2>ATS Score</h2>
                        <div style="position: relative; width: 150px; height: 150px; margin: 0 auto;">
                            <div style="
                                position: absolute;
                                width: 150px;
                                height: 150px;
                                border-radius: 50%;
                                background: conic-gradient(
                                    #4CAF50 0% {score}%,
                                    #2c2c2c {score}% 100%
                                );
                                display: flex;
                                align-items: center;
                                justify-content: center;
                            ">
                                <div style="
                                    width: 120px;
                                    height: 120px;
                                    background: #1a1a1a;
                                    border-radius: 50%;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-size: 24px;
                                    font-weight: bold;
                                    color: {color};
                                ">
                                    {score}
                                </div>
                            </div>
                        </div>
                        <div style="text-align: center; margin-top: 10px;">
                            <span style="
                                font-size: 1.2em;
                                color: {color};
                                font-weight: bold;
                            ">
                                {status}
                            </span>
                        </div>
                    """.format(
                        score=analysis['ats_score'],
                        color='#4CAF50' if analysis['ats_score'] >= 80 else '#FFA500' if analysis['ats_score'] >= 60 else '#FF4444',
                        status='Excellent' if analysis['ats_score'] >= 80 else 'Good' if analysis['ats_score'] >= 60 else 'Needs Improvement'
                    ), unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                                        
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Skills Match</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Keyword Match", f"{int(analysis.get('keyword_match', {}).get('score', 0))}%")
                    
                    if analysis['keyword_match']['missing_skills']:
                        st.markdown("#### Missing Skills:")
                        for skill in analysis['keyword_match']['missing_skills']:
                            st.markdown(f"- {skill}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div class="feature-card">
                        <h2>Format Analysis</h2>
                    """, unsafe_allow_html=True)
                    
                    st.metric("Format Score", f"{int(analysis.get('format_score', 0))}%")
                    st.metric("Section Score", f"{int(analysis.get('section_score', 0))}%")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("""
                    <div class="feature-card">
                        <h2>📋 Resume Improvement Suggestions</h2>
                    """, unsafe_allow_html=True)
                    
                    # Contact Section
                    if analysis.get('contact_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📞 Contact Information</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('contact_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Summary Section
                    if analysis.get('summary_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📝 Professional Summary</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('summary_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Skills Section
                    if analysis.get('skills_suggestions') or analysis['keyword_match']['missing_skills']:
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎯 Skills</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('skills_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        if analysis['keyword_match']['missing_skills']:
                            st.markdown("<li style='margin-bottom: 8px;'>✓ Consider adding these relevant skills:</li>", unsafe_allow_html=True)
                            for skill in analysis['keyword_match']['missing_skills']:
                                st.markdown(f"<li style='margin-left: 20px; margin-bottom: 4px;'>• {skill}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Experience Section
                    if analysis.get('experience_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>💼 Work Experience</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('experience_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # Education Section
                    if analysis.get('education_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>🎓 Education</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('education_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    # General Formatting Suggestions
                    if analysis.get('format_suggestions'):
                        st.markdown("""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h3 style='color: #4CAF50; margin-bottom: 10px;'>📄 Formatting</h3>
                            <ul style='list-style-type: none; padding-left: 0;'>
                        """, unsafe_allow_html=True)
                        for suggestion in analysis.get('format_suggestions', []):
                            st.markdown(f"<li style='margin-bottom: 8px;'>✓ {suggestion}</li>", unsafe_allow_html=True)
                        st.markdown("</ul></div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                

                
                # Course Recommendations
                st.markdown("""
                <div class="feature-card">
                    <h2>📚 Recommended Courses</h2>
                """, unsafe_allow_html=True)
                
                courses = get_courses_for_role(selected_role)
                if not courses:
                    category = get_category_for_role(selected_role)
                    courses = COURSES_BY_CATEGORY.get(category, {}).get(selected_role, [])
                
                cols = st.columns(2)
                for i, course in enumerate(courses[:6]):  # Show top 6 courses
                    with cols[i % 2]:
                        st.markdown(f"""
                        <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 10px 0;'>
                            <h4>{course[0]}</h4>
                            <a href='{course[1]}' target='_blank'>View Course</a>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("""
                <div class="feature-card">
                    <h2>📺 Helpful Videos</h2>
                """, unsafe_allow_html=True)
                
                tab1, tab2 = st.tabs(["Resume Tips", "Interview Tips"])
                
                with tab1:
                    for category, videos in RESUME_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                with tab2:
                    for category, videos in INTERVIEW_VIDEOS.items():
                        st.subheader(category)
                        cols = st.columns(2)
                        for i, video in enumerate(videos):
                            with cols[i % 2]:
                                st.video(video[1])
                
                st.markdown("</div>", unsafe_allow_html=True)
                
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>© Aastha</p>", unsafe_allow_html=True)


    def render_home(self):
        apply_modern_styles()

        section_header(
            "AI Powered Resume Analyzer",
            "Transform your career with AI-powered resume analysis and professional resume building."
        )

        st.markdown(
            """
            <div style="
                text-align: left;
                font-size: 1.65rem;
                margin-bottom: 2.1rem;
                font-weight: 600;
                letter-spacing: 0.01em;
                border-bottom: 2px solid #00c6ff;
                display: inline-block;
                padding-bottom: 0.3rem;
                background: none;
            ">
                Here are the following features in this project
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <style>
            .modern-feature-cards {
                display: flex;
                gap: 2rem;
                flex-wrap: wrap;
                justify-content: center;
                margin: 2.5rem 0 2rem 0;
            }
            .modern-feature-card {
                background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
                border-radius: 1.5rem;
                box-shadow: 0 6px 24px rgba(0,0,0,0.13);
                padding: 2.2rem 2rem 1.7rem 2rem;
                min-width: 270px;
                max-width: 320px;
                flex: 1 1 270px;
                color: white;
                text-align: center;
                position: relative;
                transition: transform 0.25s cubic-bezier(.4,0,.2,1), box-shadow 0.25s cubic-bezier(.4,0,.2,1);
                cursor: pointer;
                margin-bottom: 1rem;
                border: none;
                outline: none;
            }
            .modern-feature-card:hover {
                transform: translateY(-10px) scale(1.035);
                box-shadow: 0 14px 40px rgba(0,198,255,0.23), 0 2px 8px rgba(0,0,0,0.07);
            }
            .modern-feature-icon {
                font-size: 2.8rem;
                margin-bottom: 1.1rem;
                background: linear-gradient(135deg, #fff 0%, #00c6ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            .modern-feature-title {
                font-size: 1.45rem;
                font-weight: 700;
                margin-bottom: 0.7rem;
                letter-spacing: 0.01em;
            }
            .modern-feature-desc {
                font-size: 1.05rem;
                color: #e6f7ff;
                margin-bottom: 0.1rem;
                font-weight: 400;
                line-height: 1.55;
            }
            .project-desc-section {
                background: linear-gradient(90deg, #005C97 0%, #363795 100%);
                border-radius: 16px;
                padding: 2.2rem 1.5rem 2.2rem 1.5rem;
                margin: 2rem auto 2.5rem auto;
                max-width: 650px;
                text-align: center;
                box-shadow: 0 4px 24px rgba(0,0,0,0.12);
            }
            .project-desc-title {
                color: #fff;
                font-size: 2.1rem;
                font-weight: 700;
                margin-bottom: 0.7rem;
                letter-spacing: 0.01em;
            }
            .project-desc-text {
                color: #d9e4f5;
                font-size: 1.15rem;
                font-weight: 400;
                margin-bottom: 0.1rem;
                line-height: 1.7;
            }
            /* Styled HR Separator */
            .section-separator-hr {
                border: none;
                height: 3px;
                margin: 2.5rem auto 2.5rem auto;
                width: 70%;
                background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
                border-radius: 2px;
                opacity: 0.7;
                box-shadow: 0 2px 8px rgba(0,198,255,0.08);
            }
            /* Why Choose Section */
            .why-choose-section {
                background: linear-gradient(90deg, #232526 0%, #414345 100%);
                border-radius: 16px;
                padding: 2.1rem 1.5rem 2.1rem 1.5rem;
                margin: 2.5rem auto 2.5rem auto;
                max-width: 800px;
                box-shadow: 0 2px 16px rgba(0,0,0,0.13);
            }
            .why-choose-title {
                color: #00c6ff;
                font-size: 1.7rem;
                font-weight: 700;
                margin-bottom: 1.0rem;
                letter-spacing: 0.01em;
                text-align: center;
            }
            .why-choose-features {
                display: flex;
                justify-content: center;
                gap: 2.5rem;
                flex-wrap: wrap;
                margin-top: 1.3rem;
            }
            .why-choose-feature {
                background: linear-gradient(120deg, #00c6ff 0%, #0072ff 100%);
                border-radius: 1rem;
                padding: 1.2rem 1.1rem;
                min-width: 170px;
                color: #fff;
                font-weight: 600;
                font-size: 1.13rem;
                text-align: center;
                margin-bottom: 0.7rem;
                box-shadow: 0 2px 10px rgba(0,198,255,0.08);
                transition: transform 0.2s;
            }
            .why-choose-feature:hover {
                transform: translateY(-4px) scale(1.035);
            }
            /* Testimonials Section */
            .testimonials-section {
                background: linear-gradient(90deg, #232526 0%, #414345 100%);
                border-radius: 16px;
                padding: 2.1rem 1.5rem 2.1rem 1.5rem;
                margin: 2.5rem auto 2.5rem auto;
                max-width: 800px;
                box-shadow: 0 2px 16px rgba(0,0,0,0.13);
                text-align: center;
            }
            .testimonials-title {
                color: #00c6ff;
                font-size: 1.7rem;
                font-weight: 700;
                margin-bottom: 1.0rem;
                letter-spacing: 0.01em;
            }
            .testimonial-cards {
                display: flex;
                gap: 2rem;
                flex-wrap: wrap;
                justify-content: center;
                margin-top: 1.3rem;
            }
            .testimonial-card {
                background: linear-gradient(120deg, #0072ff 0%, #00c6ff 100%);
                border-radius: 1rem;
                padding: 1.3rem 1.1rem;
                min-width: 230px;
                max-width: 320px;
                color: #fff;
                font-size: 1.07rem;
                margin-bottom: 0.7rem;
                box-shadow: 0 2px 10px rgba(0,198,255,0.08);
                position: relative;
                text-align: left;
            }
            .testimonial-quote {
                font-style: italic;
                font-size: 1.08rem;
                margin-bottom: 0.8rem;
            }
            .testimonial-author {
                font-weight: 700;
                color: #fff;
                font-size: 1.02rem;
            }
            .testimonial-role {
                font-size: 0.96rem;
                color: #e6f7ff;
            }
            /* CTA Section */
            .cta-section {
                background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
                border-radius: 1.5rem;
                padding: 2.3rem 1.5rem 2.3rem 1.5rem;
                margin: 3rem auto 1.5rem auto;
                max-width: 700px;
                box-shadow: 0 4px 24px rgba(0,198,255,0.13);
                text-align: center;
                color: #fff;
            }
            .cta-title {
                font-size: 2.0rem;
                font-weight: 700;
                margin-bottom: 1.1rem;
                letter-spacing: 0.01em;
            }
            .cta-desc {
                font-size: 1.16rem;
                margin-bottom: 1.7rem;
                line-height: 1.6;
            }
            .cta-btn {
                background: #fff;
                color: #0072ff;
                font-weight: 700;
                font-size: 1.13rem;
                padding: 1rem 2.4rem;
                border-radius: 50px;
                border: none;
                cursor: pointer;
                transition: background 0.2s, color 0.2s, transform 0.18s;
                box-shadow: 0 2px 12px rgba(0,198,255,0.08);
                text-decoration: none;
                display: inline-block;
            }
            .cta-btn:hover {
                background: #0072ff;
                color: #fff;
                transform: translateY(-2px) scale(1.04);
            }
            @media (max-width: 900px) {
                .modern-feature-cards {
                    flex-direction: column;
                    align-items: center;
                }
                .modern-feature-card {
                    max-width: 100%;
                    min-width: 0;
                }
                .project-desc-section, .why-choose-section, .testimonials-section, .cta-section {
                    max-width: 100%;
                    padding: 1.2rem 0.7rem 1.2rem 0.7rem;
                }
                .project-desc-title, .why-choose-title, .testimonials-title, .cta-title {
                    font-size: 1.45rem;
                }
                .project-desc-text, .cta-desc {
                    font-size: 1rem;
                }
                .section-separator-hr {
                    width: 96%;
                    margin: 2rem auto 2rem auto;
                }
                .why-choose-features, .testimonial-cards {
                    flex-direction: column;
                    gap: 1rem;
                }
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="modern-feature-cards">
                <div class="modern-feature-card" onclick="window.dispatchEvent(new CustomEvent('featureCardClick', {detail: '🔍 RESUME ANALYZER'}));">
                    <div class="modern-feature-icon"><i class="fas fa-robot"></i></div>
                    <div class="modern-feature-title">AI-Powered Analysis</div>
                    <div class="modern-feature-desc">Get instant feedback on your resume with advanced AI analysis.</div>
                </div>
                <div class="modern-feature-card" onclick="window.dispatchEvent(new CustomEvent('featureCardClick', {detail: '📝 RESUME BUILDER'}));">
                    <div class="modern-feature-icon"><i class="fas fa-file-alt"></i></div>
                    <div class="modern-feature-title">Smart Resume Builder</div>
                    <div class="modern-feature-desc">Create professional resumes with our intelligent builder.</div>
                </div>
            </div>
            <script>
            if (typeof window.featureCardHandlerSet === 'undefined') {
                window.featureCardHandlerSet = true;
                window.addEventListener('featureCardClick', e => {
                    const detail = e.detail;
                    const streamlitEvents = window.streamlitEvents || window.parent.streamlitEvents;
                    if (window.streamlitSendMessage) {
                        window.streamlitSendMessage('streamlit:setComponentValue', {key: 'feature_card_click', value: detail});
                    } else if (streamlitEvents) {
                        streamlitEvents.send('streamlit:setComponentValue', {key: 'feature_card_click', value: detail});
                    }
                });
            }
            </script>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="why-choose-section">
                <div class="why-choose-title">Why Choose This App?</div>
                <div class="why-choose-features">
                    <div class="why-choose-feature">
                        <i class="fas fa-brain" style="font-size: 1.7rem; margin-bottom: 0.5rem;"></i><br>
                        AI-Powered Insights
                    </div>
                    <div class="why-choose-feature">
                        <i class="fas fa-search" style="font-size: 1.7rem; margin-bottom: 0.5rem;"></i><br>
                        ATS Optimization
                    </div>
                    <div class="why-choose-feature">
                        <i class="fas fa-user-check" style="font-size: 1.7rem; margin-bottom: 0.5rem;"></i><br>
                        Personalized Suggestions
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="testimonials-section">
                <div class="testimonials-title">What Users Are Saying</div>
                <div class="testimonial-cards">
                    <div class="testimonial-card">
                        <div class="testimonial-quote">
                            "This app helped me transform my resume and land more interviews. The AI feedback is spot on and easy to understand!"
                        </div>
                        <div class="testimonial-author">Priya Sharma</div>
                        <div class="testimonial-role">Software Engineer</div>
                    </div>
                    <div class="testimonial-card">
                        <div class="testimonial-quote">
                            "The resume builder is intuitive, and the ATS optimization suggestions really made a difference in my job search."
                        </div>
                        <div class="testimonial-author">Rahul Verma</div>
                        <div class="testimonial-role">Recent Graduate</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <hr class="section-separator-hr" />
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="project-desc-section">
                <div class="project-desc-title">About This Project</div>
                <div class="project-desc-text">
                    AI Powered Resume Analyzer is a modern web application designed to help job seekers build professional, ATS-friendly resumes and receive instant, actionable feedback using advanced AI. Effortlessly create, analyze, and improve your resume to stand out in today's competitive job market. <br><br>
                    <b>Features:</b> Smart resume builder, AI-driven analysis, personalized suggestions, and a sleek, user-friendly interface—all in one place.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="cta-section">
                <div class="cta-title">Ready to Get Started?</div>
                <div class="cta-desc">
                    Upload your resume for instant AI-powered analysis or build a professional resume from scratch in minutes. <br>
                    Take your career to the next level now!
                </div>
                <a href="#" onclick="window.dispatchEvent(new CustomEvent('featureCardClick', {detail: '🔍 RESUME ANALYZER'})); return false;" class="cta-btn" style="margin-right: 1.2rem;">Analyze Resume</a>
                <a href="#" onclick="window.dispatchEvent(new CustomEvent('featureCardClick', {detail: '📝 RESUME BUILDER'})); return false;" class="cta-btn">Build Resume</a>
            </div>
            """,
            unsafe_allow_html=True
        )

        feature_clicked = st.query_params.get("feature_card_click", [None])[0]
        if "feature_card_click" in st.session_state:
            feature_clicked = st.session_state.pop("feature_card_click")
        if feature_clicked:
            mapping = {
                "🔍 RESUME ANALYZER": "resume_analyzer",
                "📝 RESUME BUILDER": "resume_builder",
                "🏠 HOME": "home"
            }
            if feature_clicked in mapping:
                st.session_state.page = mapping[feature_clicked]
                st.rerun()

        st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>© Manjot Singh</p>", unsafe_allow_html=True)

    def main(self):
        """Main application entry point"""
        set_sidebar_style()
        self.apply_global_styles()
        
        with st.sidebar:
            lottie_animation = self.load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_xyadoh9h.json")
            if lottie_animation:
                st_lottie(lottie_animation, height=200, key="sidebar_animation")
            else:
                st.info("⚙️ Animation failed to load. Please check your internet connection.")
            st.title("AI Powered Resume Analyzer")
            st.markdown("---")
            
            for page_name in self.pages.keys():
                if st.button(page_name, use_container_width=True):
                    cleaned_name = page_name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").strip()
                    st.session_state.page = cleaned_name
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.session_state.get('is_admin', False):
                st.success(f"Logged in as: {st.session_state.get('current_admin_email')}")
                if st.button("Logout", key="logout_button"):
                    try:
                        log_admin_action(st.session_state.get('current_admin_email'), "logout")
                        st.session_state.is_admin = False
                        st.session_state.current_admin_email = None
                        st.success("Logged out successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during logout: {str(e)}")
        
        if 'initial_load' not in st.session_state:
            st.session_state.initial_load = True
            st.session_state.page = 'home'
            st.rerun()
        
        current_page = st.session_state.get('page', 'home')
        
        page_mapping = {name.lower().replace(" ", "_").replace("🏠", "").replace("🔍", "").replace("📝", "").strip(): name 
                       for name in self.pages.keys()}
        
        if current_page in page_mapping:
            self.pages[page_mapping[current_page]]()
        else:
            self.render_home()
    
if __name__ == "__main__":
    app = ResumeApp()
    app.main()
