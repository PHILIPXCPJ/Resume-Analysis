import re
import spacy
from typing import Dict, List, Optional

nlp = spacy.load("en_core_web_sm")

class ResumeParser:
    def __init__(self):
        self.skill_keywords = {
            'accounting': ['general ledger', 'accounts payable', 'financial reporting', 'GAAP', 
                          'reconciliation', 'budgeting', 'ERP', 'DEAMS', 'GAFS'],
            'finance': ['financial analysis', 'cost accounting', 'auditing', 'tax accounting',
                       'financial planning', 'forecasting', 'FMFIA'],
            'tools': ['Excel', 'SAP', 'Oracle', 'QuickBooks', 'DTS', 'Louis II'],
            'management': ['team leadership', 'process improvement', 'strategic planning',
                         'performance metrics', 'compliance']
        }
        
        # Common section headers in resumes
        self.section_headers = [
            'experience', 'education', 'skills', 'certifications',
            'accomplishments', 'summary', 'highlights'
        ]

    def extract_sections(self, text: str) -> Dict[str, str]:
        """Split resume into sections based on common headers"""
        sections = {}
        current_section = "preamble"
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.strip().lower()
            # Check if line is a section header
            if any(header in line_lower for header in self.section_headers):
                current_section = line_lower
                sections[current_section] = []
            elif current_section:
                if line.strip():  # Skip empty lines
                    sections.setdefault(current_section, []).append(line.strip())
        
        # Join the lines for each section
        return {section: '\n'.join(content) for section, content in sections.items()}

    def extract_contact(self, text: str) -> Dict:
        """Improved contact information extraction"""
        doc = nlp(text)
        
        # Extract emails
        emails = list(set(token.text for token in doc if token.like_email))
        
        # Improved phone number regex
        phones = re.findall(
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            text
        )
        
        # Name extraction - look for all caps or title case names early in document
        name = None
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) >= 2:
                name = ent.text
                break
        
        # Fallback: Look for lines that might contain name
        if not name:
            for line in text.split('\n')[:10]:  # Check first 10 lines
                if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', line.strip()):
                    name = line.strip()
                    break
        
        return {
            "name": name or "Not Found",
            "emails": emails,
            "phones": list(set(phones)),
            "location": self.extract_location(text)
        }

    def extract_location(self, text: str) -> Optional[str]:
        """Extract location from experience entries"""
        # Look for city/state patterns in experience lines
        location_match = re.search(
            r'[A-Z][a-zA-Z]+\s*,\s*[A-Z]{2}',
            text
        )
        return location_match.group(0) if location_match else None

    def extract_experience(self, text: str) -> List[Dict]:
        """Parse work experience with dates and position"""
        experience = []
        sections = self.extract_sections(text)
        exp_text = sections.get('experience', '')
        
        if not exp_text:
            # Fallback: Look for experience-like text
            date_pattern = r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b|\b\d{4}\b)'
            exp_pattern = rf'(.+?)\s*(?:{date_pattern}\s*to\s*{date_pattern}|{date_pattern}\s*-\s*{date_pattern}|present)'
            
            matches = re.finditer(
                rf'(.+?)\s*({date_pattern}\s*(?:to|–|-)\s*{date_pattern}|present).+?(?=\n\w|\Z)',
                text,
                re.DOTALL
            )
            
            for match in matches:
                position = match.group(1).strip()
                dates = match.group(2)
                description = match.group(0).replace(position, '').replace(dates, '').strip()
                
                experience.append({
                    "position": position,
                    "dates": dates,
                    "description": description
                })
        else:
            # Parse structured experience section
            entries = re.split(r'\n(?=\w)', exp_text)
            for entry in entries:
                # Look for position and dates
                date_match = re.search(
                    r'(.+?)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\s+to\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\d{4}\s+to\s+\d{4}|present)',
                    entry
                )
                if date_match:
                    position = date_match.group(1).strip()
                    dates = date_match.group(2).strip()
                    description = entry.replace(position, '').replace(dates, '').strip()
                    
                    experience.append({
                        "position": position,
                        "dates": dates,
                        "description": description
                    })
        
        return experience[:10]  # Return first 10 experiences

    def extract_education(self, text: str) -> List[Dict]:
        """Extract education with degrees and dates"""
        education = []
        sections = self.extract_sections(text)
        edu_text = sections.get('education', '')
        
        if not edu_text:
            # Fallback pattern
            edu_pattern = r'(.+?)\s*,\s*(\d{4})\s*(?:-|to)\s*(\d{4}|present)'
            matches = re.finditer(edu_pattern, text)
            for match in matches:
                education.append({
                    "institution": match.group(1).strip(),
                    "degree": "",
                    "year": match.group(3).strip()
                })
        else:
            # Parse structured education section
            entries = re.split(r'\n(?=\w)', edu_text)
            for entry in entries:
                # Look for degree patterns
                degree_match = re.search(
                    r'(.+?)\s*,\s*(.+?)\s*,\s*(\d{4})',
                    entry
                )
                if degree_match:
                    education.append({
                        "institution": degree_match.group(1).strip(),
                        "degree": degree_match.group(2).strip(),
                        "year": degree_match.group(3).strip()
                    })
                else:
                    # Fallback - just capture the line
                    education.append({
                        "institution": entry.strip(),
                        "degree": "",
                        "year": ""
                    })
        
        return education[:5]  # Return first 5 education entries

    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Categorize skills with context awareness"""
        found_skills = {category: [] for category in self.skill_keywords}
        sections = self.extract_sections(text)
        
        # Check skills section first
        skills_text = sections.get('skills', '') + sections.get('highlights', '')
        
        # Then check entire text if no skills section
        if not skills_text.strip():
            skills_text = text
            
        for category, keywords in self.skill_keywords.items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', skills_text, re.IGNORECASE):
                    found_skills[category].append(keyword)
        
        return found_skills

    def parse(self, text: str) -> Dict:
        """Main parsing method with improved structure"""
        sections = self.extract_sections(text)
        
        return {
            "contact": self.extract_contact(text),
            "experience": self.extract_experience(text),
            "education": self.extract_education(text),
            "skills": self.extract_skills(text),
            "sections": list(sections.keys()),  # Show detected sections
            "raw_text": text[:1000] + "..." if len(text) > 1000 else text
        }