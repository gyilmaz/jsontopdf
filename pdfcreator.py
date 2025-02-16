import json
import os
import boto3
import tempfile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
import json
from reportlab.platypus import PageBreak, KeepTogether

# -------------------------------
# Register your custom fonts
# -------------------------------
# Ensure you have downloaded these files and they are in the same directory as this script.
# For example, download MarkaziText-Regular.ttf and MarkaziText-Bold.ttf from a trusted source.
pdfmetrics.registerFont(TTFont('MarkaziText', 'MarkaziText-Regular.ttf'))
pdfmetrics.registerFont(TTFont('MarkaziText-Bold', 'MarkaziText-Bold.ttf'))

# Optionally, register a font family so that ReportLab knows which bold/italic fonts to use.
pdfmetrics.registerFontFamily('MarkaziTextFamily', 
                              normal='MarkaziText',
                              bold='MarkaziText-Bold')

class ResumeGenerator:
    def __init__(self, data):
        self.data = data
        self.doc = SimpleDocTemplate(
            "resume.pdf",
            pagesize=letter,
            rightMargin=inch,
            leftMargin=inch,
            topMargin=0.1 * inch,
            bottomMargin=0.5 * inch
        )
        self.section_mapping = {
        "basics": self.create_header,
        "work": self.create_experience_section,
        "volunteer": self.create_volunteer_section,
        "education": self.create_education_section,
        "awards": self.create_awards_section,         # Define this method if needed.
        "publications": self.create_publications_section,
        "skills": self.create_skills_section,
        "languages": self.create_languages_section,
        "interests": self.create_interests_section,
        "references": self.create_references_section,
        "projects": self.create_projects_section
        }
        self.styles = getSampleStyleSheet()
        
        # Name style (16pt, bold, centered) using custom font
        self.styles.add(ParagraphStyle(
            name='ResumeName',
            fontSize=16,
            spaceAfter=6,
            alignment=1,  # Center alignment
            fontName='MarkaziText-Bold'
        ))
        
        # Section headers (12pt, bold) using custom font
        self.styles.add(ParagraphStyle(
            name='ResumeSectionHeader',
            fontSize=12,
            spaceBefore=8,
            spaceAfter=0,
            fontName='MarkaziText-Bold',
            textTransform='uppercase'
        ))
        
        # Job titles (11pt, bold) using custom font
        self.styles.add(ParagraphStyle(
            name='ResumeJobHeader',
            fontSize=11,
            spaceBefore=6,
            spaceAfter=2,
            fontName='MarkaziText-Bold',
            leading=13
        ))
        
        # Body text (10pt) using custom regular font
        self.styles.add(ParagraphStyle(
            name='ResumeBody',
            fontSize=10,
            leading=12,
            spaceBefore=1,
            spaceAfter=1,
            fontName='MarkaziText'
        ))
        
        # Contact info style (centered) using custom regular font
        self.styles.add(ParagraphStyle(
            name='ResumeContact',
            fontSize=10,
            spaceAfter=6,
            alignment=1,  # Center alignment
            fontName='MarkaziText'
        ))
    
    def create_header_line(self, extra_space_after=3):
        """
        Creates a spacer, a horizontal line, and another spacer.
        This will be used immediately after section headers.
        """
        return [
            Spacer(1, 3),
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.black,
                spaceBefore=0,
                spaceAfter=0
            ),
            Spacer(1, extra_space_after)
        ]

    def create_header(self):
        elements = []
        basics = self.data.get('basics', {})

        if basics.get('name'):
            elements.append(Paragraph(basics['name'], self.styles['ResumeName']))

        if basics.get('label'):
            elements.append(Paragraph(
                f"<b>{basics['label']}</b>",
                ParagraphStyle('ResumeTitle', parent=self.styles['ResumeBody'], alignment=1)
            ))

        # Contact info parts
        contact_parts = []
        if basics.get('email'):
            contact_parts.append(basics['email'])
        if basics.get('phone'):
            contact_parts.append(basics['phone'])

        location = basics.get('location', {})
        if location.get('city') and location.get('region'):
            contact_parts.append(f"{location['city']}, {location['region']}")

        # Include the URL if provided
        if basics.get('url'):
            contact_parts.append(basics['url'])

        if contact_parts:
            elements.append(Paragraph(
                ' | '.join(contact_parts),
                self.styles['ResumeContact']
            ))

        # Include profiles if available
        profiles = basics.get('profiles', [])
        if profiles:
            profile_parts = []
            for profile in profiles:
                if profile.get('network') and profile.get('username'):
                    # Use hyperlink formatting if the URL is provided.
                    if profile.get('url'):
                        profile_parts.append(
                            f"<b>{profile['network']}</b>: <a href='{profile['url']}' color='blue'>{profile['username']}</a>"
                        )
                    else:
                        profile_parts.append(f"<b>{profile['network']}</b>: {profile['username']}")
            if profile_parts:
                elements.append(Paragraph(
                    ' | '.join(profile_parts),
                    self.styles['ResumeContact']
                ))

        if basics.get('summary'):
            elements.append(Paragraph(basics['summary'], self.styles['ResumeBody']))
        return elements

    def create_skills_section(self):
        """Create the skills section if data exists."""
        section = []  # Local list for this section
        skills = self.data.get('skills')
        if not skills:
            return []
        
        section.append(Paragraph('SKILLS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
            
        for skill in skills:
            if isinstance(skill, dict) and skill.get('name') and skill.get('keywords'):
                skill_text = f"<b>{skill['name']}:</b> {', '.join(skill['keywords'])}"
                section.append(Paragraph(skill_text, self.styles['ResumeBody']))
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]

    def create_experience_section(self):
        """Create the work experience section if data exists."""
        elements = []
        work = self.data.get('work')
        if not work:
            return elements
        
        elements.append(Paragraph('EXPERIENCE', self.styles['ResumeSectionHeader']))
        elements.extend(self.create_header_line())
        
        section = []
        for job in work:
            if isinstance(job, dict):
                # Prepare the title (company and position) for the left column.
                company = job.get('company', '') or job.get('name', '')
                position = job.get('position', '')
                title_paragraph = Paragraph(
                    f"<b>{company} - {position}</b>",
                    self.styles['ResumeJobHeader']
                )
                
                # Prepare the location and dates for the right column.
                location = job.get('location', '')
                dates = f"{job.get('startDate', '')} - {job.get('endDate', '')}"
                dates_paragraph = Paragraph(
                    f"{location} | {dates}",
                    ParagraphStyle(
                        'ResumeDateLoc',
                        parent=self.styles['ResumeBody'],
                        textColor=colors.gray,
                        spaceAfter=4,
                        alignment=2  # Right alignment
                    )
                )
                
                # Create a table with two columns.
                data = [[title_paragraph, dates_paragraph]]
                table = Table(data, colWidths=[None, 150])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                section.append(table)
                
                # Add highlights (if any) below the title/date row.
                if job.get('highlights'):
                    for highlight in job['highlights']:
                        section.append(Paragraph(
                            f"• {highlight}",
                            self.styles['ResumeBody']
                        ))
                section.append(Spacer(1, 4))
        
        elements.append(KeepTogether(section))
        elements.append(Spacer(1, 5))
        return elements

    def create_education_section(self):
        section = []
        education = self.data.get('education')
        if not education:
            return []
        
        section.append(Paragraph('EDUCATION', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for edu in education:
            if isinstance(edu, dict):
                # Build degree information (e.g., "Bachelor, Information Technology")
                degree_parts = []
                if edu.get('studyType'):
                    degree_parts.append(edu['studyType'])
                if edu.get('area'):
                    degree_parts.append(edu['area'])
                degree_text = f"<b>{', '.join(degree_parts)}</b>" if degree_parts else ""
                left_para = Paragraph(degree_text, self.styles['ResumeBody'])
                
                # Prepare date and score info (right aligned)
                date_info = []
                start = edu.get('startDate', '')
                end = edu.get('endDate', '')
                if start or end:
                    # Ensure no stray hyphen when one date is missing.
                    date_range = f"{start} - {end}".strip(" -")
                    date_info.append(date_range)
                if edu.get('score'):
                    date_info.append(f"Score: {edu['score']}")
                right_text = " | ".join(date_info)
                right_para = Paragraph(
                    right_text,
                    ParagraphStyle(
                        'EduDateStyle',
                        parent=self.styles['ResumeBody'],
                        textColor=colors.gray,
                        alignment=2,  # Right alignment
                        spaceAfter=2
                    )
                )
                
                # Create a table with two columns:
                # Left: degree information
                # Right: date and score info (right aligned)
                data = [[left_para, right_para]]
                table = Table(data, colWidths=[None, 150])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                section.append(table)
                
                # Display institution name as a separate line.
                if edu.get('institution'):
                    institution_text = edu['institution']
                    if edu.get('url'):
                        institution_text = f"<a href='{edu['url']}' color='blue'>{edu['institution']}</a>"
                    institution_para = Paragraph(
                        institution_text,
                        ParagraphStyle(
                            'ResumeInstitution',
                            parent=self.styles['ResumeBody'],
                            textColor=colors.gray,
                            spaceAfter=2
                        )
                    )
                    section.append(institution_para)
                
                # Optionally list courses if provided.
                if edu.get('courses'):
                    courses_text = ', '.join(edu['courses'])
                    section.append(Paragraph(f"Courses: {courses_text}", self.styles['ResumeBody']))
                
                section.append(Spacer(1, 4))
        
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]

    def create_certificates_section(self):
        """Create the certificates section if data exists."""
        section = []
        certificates = self.data.get('certificates')
        if not certificates:
            return section
        
        section.append(Paragraph('CERTIFICATIONS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for cert in certificates:
            if isinstance(cert, dict) and cert.get('name'):
                cert_text = cert['name']
                if cert.get('issuer'):
                    cert_text += f" - {cert['issuer']}"
                section.append(Paragraph(
                    f"• {cert_text}",
                    self.styles['ResumeBody']
                ))
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]

    def create_projects_section(self):
        """Create the projects section if data exists."""
        section = []
        projects = self.data.get('projects')
        if not projects:
            return section
        
        section.append(Paragraph('PROJECTS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for proj in projects:
            if isinstance(proj, dict):
                # Project name as header.
                if proj.get('name'):
                    section.append(Paragraph(
                        f"<b>{proj['name']}</b>",
                        self.styles['ResumeJobHeader']
                    ))
                # Project description.
                if proj.get('description'):
                    section.append(Paragraph(proj['description'], self.styles['ResumeBody']))
                # Project highlights.
                if proj.get('highlights'):
                    for highlight in proj['highlights']:
                        section.append(Paragraph(
                            f"• {highlight}",
                            self.styles['ResumeBody']
                        ))
                section.append(Spacer(1, 4))
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_references_section(self):
        section = []
        references = self.data.get('references')
        if not references:
            return section

        section.append(Paragraph('REFERENCES', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for ref in references:
            if isinstance(ref, dict):
                # Display the reference's name as the header.
                if ref.get('name'):
                    section.append(Paragraph(
                        f"<b>{ref['name']}</b>",
                        self.styles['ResumeJobHeader']
                    ))
                # Display the reference text.
                if ref.get('reference'):
                    section.append(Paragraph(ref['reference'], self.styles['ResumeBody']))
                section.append(Spacer(1, 4))
        
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_interests_section(self):
        section = []
        interests = self.data.get('interests')
        if not interests:
            return section
        
        section.append(Paragraph('INTERESTS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for interest in interests:
            if isinstance(interest, dict) and interest.get('name') and interest.get('keywords'):
                interest_text = f"<b>{interest['name']}</b>: {', '.join(interest['keywords'])}"
                section.append(Paragraph(interest_text, self.styles['ResumeBody']))
        
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_languages_section(self):
        section = []
        languages = self.data.get('languages')
        if not languages:
            return section
        
        section.append(Paragraph('LANGUAGES', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for lang in languages:
            if isinstance(lang, dict) and lang.get('language') and lang.get('fluency'):
                lang_text = f"<b>{lang['language']}</b>: {lang['fluency']}"
                section.append(Paragraph(lang_text, self.styles['ResumeBody']))
        
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_publications_section(self):
        section = []
        publications = self.data.get('publications')
        if not publications:
            return section

        section.append(Paragraph('PUBLICATIONS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())
        
        for pub in publications:
            if isinstance(pub, dict):
                # Publication name as header.
                if pub.get('name'):
                    section.append(Paragraph(
                        f"<b>{pub['name']}</b>",
                        self.styles['ResumeJobHeader']
                    ))
                
                # Create a table for publisher and release date.
                publisher_text = pub.get('publisher', '')
                release_date_text = pub.get('releaseDate', '')
                
                publisher_para = Paragraph(
                    publisher_text,
                    self.styles['ResumeBody']
                ) if publisher_text else Paragraph("", self.styles['ResumeBody'])
                
                release_para = Paragraph(
                    release_date_text,
                    ParagraphStyle(
                        'PubDateStyle',
                        parent=self.styles['ResumeBody'],
                        textColor=colors.gray,
                        alignment=2,  # Right alignment
                        spaceAfter=4
                    )
                ) if release_date_text else Paragraph("", self.styles['ResumeBody'])
                
                # Create a table with two columns: left for publisher, right for release date.
                data = [[publisher_para, release_para]]
                table = Table(data, colWidths=[None, 100])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                section.append(table)
                
                # URL (if provided)
                if pub.get('url'):
                    section.append(Paragraph(pub['url'], self.styles['ResumeBody']))
                # Summary of the publication.
                if pub.get('summary'):
                    section.append(Paragraph(pub['summary'], self.styles['ResumeBody']))
                
                section.append(Spacer(1, 4))
        
        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_volunteer_section(self):
        section = []
        volunteer = self.data.get('volunteer')
        if not volunteer:
            return section

        section.append(Paragraph('VOLUNTEER', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())

        for vol in volunteer:
            if isinstance(vol, dict):
                organization = vol.get('organization', '')
                position = vol.get('position', '')
                title_para = Paragraph(
                    f"<b>{organization} - {position}</b>",
                    self.styles['ResumeJobHeader']
                )
                start_date = vol.get('startDate', '')
                end_date = vol.get('endDate', '')
                dates_para = Paragraph(
                    f"{start_date} - {end_date}",
                    ParagraphStyle(
                        'VolunteerDates',
                        parent=self.styles['ResumeBody'],
                        textColor=colors.gray,
                        alignment=2,  # Left alignment
                        spaceAfter=0
                    )
                )

                # Use auto width for both columns
                data = [[title_para, dates_para]]
                table = Table(data, colWidths=[None, 100])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                section.append(table)

                if vol.get('url'):
                    section.append(Paragraph(vol['url'], self.styles['ResumeBody']))

                if vol.get('summary'):
                    section.append(Paragraph(vol['summary'], self.styles['ResumeBody']))

                if vol.get('highlights'):
                    for highlight in vol['highlights']:
                        section.append(Paragraph(f"• {highlight}", self.styles['ResumeBody']))

                section.append(Spacer(1, 4))

        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    def create_awards_section(self):
        section = []
        awards = self.data.get('awards')
        if not awards:
            return section

        section.append(Paragraph('AWARDS', self.styles['ResumeSectionHeader']))
        section.extend(self.create_header_line())

        for award in awards:
            if isinstance(award, dict):
                # Prepare the title (award title and awarder)
                title = award.get('title', '')
                awarder = award.get('awarder', '')
                title_text = f"<b>{title}</b>" if title else ""
                if awarder:
                    title_text += f" - {awarder}"
                title_para = Paragraph(title_text, self.styles['ResumeJobHeader'])

                # Prepare the date info (right aligned)
                award_date = award.get('date', '')
                date_para = Paragraph(
                    award_date,
                    ParagraphStyle(
                        'AwardDates',
                        parent=self.styles['ResumeBody'],
                        textColor=colors.gray,
                        alignment=2,  # Right alignment
                        spaceAfter=0
                    )
                )

                # Create a table with two columns: left for title/awarder, right for date
                data = [[title_para, date_para]]
                table = Table(data, colWidths=[None, 100])
                table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                    ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ]))
                section.append(table)

                # Add summary if provided
                if award.get('summary'):
                    section.append(Paragraph(award['summary'], self.styles['ResumeBody']))

                section.append(Spacer(1, 4))

        section.append(Spacer(1, 5))
        return [KeepTogether(section)]
    
    # ... All your section creation methods (create_header, create_experience_section, etc.) ...

    def generate(self):
            elements = []
            
            # Iterate over the JSON keys in the order they appear.
            # For each key that has a corresponding section method and data present,
            # call the method to generate the section.
            for key in self.data.keys():
                if key in self.section_mapping:
                    # Only add the section if there is data for it.
                    if self.data.get(key):
                        section_flowables = self.section_mapping[key]()
                        if section_flowables:
                            elements.extend(section_flowables)
                            # Optionally add a page break between sections if needed.
                            # elements.append(PageBreak())
            
            self.doc.build(elements)
        
    # Example main function remains the same.
def main():
        try:
            with open('resume_data.json', 'r', encoding='utf-8') as file:
                resume_data = json.load(file)
            
            resume = ResumeGenerator(resume_data)
            resume.generate()
            print("Resume PDF generated successfully!")
            
        except FileNotFoundError:
            print("Error: resume_data.json file not found!")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in resume_data.json! Details: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
