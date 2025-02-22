# Resume PDF Generator

This Python script generates a PDF resume using the ReportLab library. It takes resume data provided in JSON format and builds a well-formatted PDF document by organizing the content into sections such as Basics, Work Experience, Education, Skills, Projects, Awards, and more.

## Features

- **Custom Fonts:** Uses custom fonts (MarkaziText and MarkaziText-Bold) loaded from a local `fonts` directory.
- **Dynamic Sections:** Supports multiple resume sections including header, work, education, skills, projects, awards, publications, volunteer, references, interests, and languages.
- **ReportLab Integration:** Leverages ReportLab’s Platypus framework to build PDF elements like Paragraphs, Tables, Spacers, and Horizontal Rules.
- **Flexible Layout:** Automatically organizes and formats resume sections based on the provided JSON data.


## Prerequisites

- Python 3.x
- ReportLab library (`pip install reportlab`)

## Usage

1. Edit `resume_data.json` with your resume information
2. Run the generator script:

```bash
python pdfcreator.py
```

3. Find your generated resume in `resume.pdf`

## Included Files

- **Font Files**: MarkaziText font family (Bold, Medium, Regular, SemiBold)
- **Data File**: `resume_data.json` (contains resume content)
- **Generator Script**: `pdfcreator.py`

## Output

The generated resume will be saved as `resume.pdf` in the project directory.

## Notes

- The output directory contains intermediate files
- Customize fonts by modifying `pdfcreator.py`
