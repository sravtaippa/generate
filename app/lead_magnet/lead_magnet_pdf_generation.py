from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak, Image as Img, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line
from pyairtable import Api,Table as airtable_obj
import os
import requests
import ast
import openai
import json
from industry_insights import get_cold_email_kpis
from client_info_parser import collect_information
from competitor_insights import get_competitors_list

# from error_logger import execute_error_block

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_CLIENT_TABLE_NAME = os.getenv("AIRTABLE_CLIENT_TABLE_NAME")
CLIENT_NAME = 'taippa_marketing'

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to fonts directory
FONTS_DIR = os.path.join(SCRIPT_DIR, 'fonts')

pdfmetrics.registerFont(TTFont('Anton', os.path.join(FONTS_DIR, 'Anton-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Poppins', os.path.join(FONTS_DIR, 'Poppins-Regular.ttf')))
pdfmetrics.registerFont(TTFont('PoppinsBold', os.path.join(FONTS_DIR, 'Poppins-Bold.ttf')))

# Getting dynamic images from client_details table specific to each client
def get_dynamic_images(table,record_id,attachment_column):
    record = table.get(record_id)
    attachments = record['fields'].get(attachment_column)
    file_names=[]
    if attachments:
        for attachment in attachments:
            image_url = attachment['url']
            file_name = "images/"+attachment['filename']
            print("\n================")
            print(f"File name: {file_name}")
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded: {file_name}")
                file_names.append(file_name)
            else:
                print(f"Failed to download: {image_url}")
    else:
        print(f"No attachments found in column '{attachment_column}' for record ID '{record_id}'.")
    return file_names

def content_formatting_list(content, is_metrics=False):
    if is_metrics:
        # Parse metrics data which comes in format:
        # 1. **Open Rate:** 25.24%
        # 2. **Click-Through Rate (CTR):** 2-5%
        # 3. **Reply Rate:** 8.5%

        metrics_lines = content.strip().split('\n')
        metrics_data = []

        descriptions = {
            "Open Rate": "The percentage of recipients who open your email",
            "Click-Through Rate (CTR)": "The percentage of recipients who click on links in your email",
            "Reply Rate": "The percentage of recipients who reply to your email"
        }

        for line in metrics_lines:
            # Extract the metric name and value
            parts = line.split(':**')
            if len(parts) == 2:
                # Clean up the metric name
                metric_name = parts[0].replace('1.', '').replace('2.', '').replace('3.', '').replace('**', '').strip()
                # Clean up the value
                value = parts[1].strip()

                # Calculate Taippa target (higher percentages)
                try:
                    if metric_name == "Open Rate":
                        raw_value = float(value.replace('%', ''))
                        taippa_target = f"{raw_value * 1.1:.2f}%"  # 10% higher
                    elif metric_name == "Click-Through Rate (CTR)":
                        if '-' in value:
                            high_end = float(value.split('-')[1].replace('%', ''))
                            taippa_target = f"{high_end * 1.3:.1f}%"  # 30% higher than high end
                        else:
                            raw_value = float(value.replace('%', ''))
                            taippa_target = f"{raw_value * 1.3:.1f}%"  # 30% higher
                    else:  # Reply Rate
                        raw_value = float(value.replace('%', ''))
                        taippa_target = f"{raw_value * 1.5:.1f}%"  # 50% higher
                except ValueError:
                    print(f"Error processing value: {value} for {metric_name}")
                    taippa_target = "N/A"

                metrics_data.append({
                    "header": metric_name,
                    "description": descriptions.get(metric_name, ""),
                    "industry_average": value,
                    "taippa_target": taippa_target
                })

        return json.dumps(metrics_data)
    else:
        prompt = f"""Format the following content into ONLY a JSON array. Do not include any other text:
        [
            {{
                "header": "Emerging Trends in Email Marketing",
                "body": ""
            }},
            {{
                "header": "1. Personalization is Driving Higher Engagement",
                "body": "Emails with personalized subject lines are 26% more likely to be opened. Using AI tools we allow SMEs to personalize content dynamically, leveraging customer behavior and preferences."
            }}
        ]

        Content: {content}"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON formatter. Only output the exact JSON array requested, with no additional text, explanations, or formatting."
                },
                {"role": "user", "content": prompt}
            ]
        )

        result = response['choices'][0]['message']['content'].strip()

        try:
            # First try to parse as is
            json.loads(result)
            return result
        except:
            # If that fails, try to clean it up
            try:
                start = result.find('[')
                end = result.rfind(']') + 1
                if start != -1 and end != 0:
                    cleaned = result[start:end]
                    json.loads(cleaned)
                    return cleaned
                else:
                    raise ValueError("Could not find valid JSON array in response")
            except Exception as e:
                print(f"Error parsing response: {result}")
                raise e


def create_personalized_pdf(user_details, output_path, image_path):
    styles = getSampleStyleSheet()

    # Style definitions with reduced spacing
    main_title = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Anton",
        fontSize=24,
        textColor=colors.HexColor("#c969f5"),
        alignment=1,
        spaceAfter=20,  # Reduced from 30
        borderPadding=15,  # Reduced from 20
        borderWidth=2,
        borderColor=colors.HexColor("#8A2BE2"),
        borderRadius=8
    )

    greeting_style = ParagraphStyle(
        "GreetingStyle",
        parent=styles["Normal"],
        fontName="PoppinsBold",
        fontSize=16,
        textColor=colors.HexColor("#f6f2f7"),
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=18  # Reduced from 20
    )

    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Anton",
        fontSize=18,
        textColor=colors.HexColor("#6292cc"),
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=22  # Reduced from 24
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=11,  # Reduced from 12
        textColor=colors.HexColor("#f6f2f7"),
        leading=14,  # Reduced from 16
        spaceAfter=6,  # Reduced from 8
        leftIndent=20,
        firstLineIndent=-10
    )

    competitor_style = ParagraphStyle(
        "CompetitorStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=10,  # Reduced from 11
        textColor=colors.HexColor("#f6f2f7"),
        leading=12,  # Reduced from 14
        spaceAfter=4,  # Reduced from 6
        leftIndent=25,
        firstLineIndent=0
    )

    metrics_header_style = ParagraphStyle(
        "MetricsHeaderStyle",
        parent=styles["Heading2"],
        fontName="Anton",
        fontSize=14,  # Reduced from 16
        textColor=colors.HexColor("#6292cc"),
        spaceBefore=12,  # Reduced from 15
        spaceAfter=3  # Reduced from 4
    )

    metrics_style = ParagraphStyle(
        "MetricsStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=10,  # Reduced from 12
        textColor=colors.HexColor("#f6f2f7"),
        leading=14,  # Reduced from 16
        spaceAfter=3,  # Reduced from 4
        leftIndent=20
    )

    highlight_style = ParagraphStyle(
        "HighlightStyle",
        parent=styles["BodyText"],
        fontName="PoppinsBold",
        fontSize=14,
        textColor=colors.HexColor("#c969f5"),
        leading=16,
        spaceBefore=12,
        spaceAfter=12,
        alignment=1
    )

    # Background and divider functions remain the same
    def draw_fancy_background(canvas, doc):
        canvas.setFillColor(colors.black)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)

        if doc.page > 0:
            canvas.setFillColor(colors.HexColor("#6292cc"))
            canvas.setFont("Anton", 12)
            page_num = f"Page {doc.page}"
            canvas.drawString(A4[0] - 72, 30, page_num)
            canvas.setStrokeColor(colors.HexColor("#6292cc"))
            canvas.line(A4[0] - 82, 25, A4[0] - 40, 25)

    def create_divider():
        drawing = Drawing(A4[0] - 100, 15)  # Reduced height
        line = Line(0, 7, A4[0] - 100, 7)
        line.strokeColor = colors.HexColor("#6292cc")
        line.strokeWidth = 1
        drawing.add(line)
        return drawing

    content = []

    # Get user details
    name = user_details.get('name', 'there')
    job_title = user_details.get('job_title', 'professional')
    industry = user_details.get('organization_industry', 'Real Estate')
    country = user_details.get('country', 'United Arab Emirates')
    if industry in ['Unknown', '']:
        industry = 'Real Estate'

    # Add title and introduction
    content.append(Paragraph("Personalized Industry Insights Report", main_title))
    content.append(create_divider())
    content.append(Spacer(1, 0.1 * inch))  # Reduced spacing
    content.append(Paragraph(f"Hi {name},", greeting_style))
    content.append(Paragraph(f"To help you stay ahead in your industry as a {job_title}, "
                             "we've prepared a tailored insights report highlighting key competitors "
                             "and market trends relevant to your business", body_style))
    content.append(Spacer(1, 0.2 * inch))  # Reduced spacing

    # Market Competitors section
    content.append(Paragraph("Your Market Competitors", section_title))
    content.append(Paragraph("Stay informed about the top players in your market:", body_style))

    # Fetch and format competitors list
    try:
        competitors = get_competitors_list(industry, country)
        if isinstance(competitors, str) and not competitors.startswith("Error"):
            competitor_lines = competitors.strip().split('\n')
            for line in competitor_lines:
                if line.strip():
                    content.append(Paragraph(line.strip(), competitor_style))
        else:
            content.append(Paragraph("Competitor data currently unavailable.", body_style))
    except Exception as e:
        print(f"Error fetching competitors: {e}")
        content.append(Paragraph("Competitor data currently unavailable.", body_style))

    content.append(Spacer(1, 0.2 * inch))

    # Industry Insights section with metrics
    content.append(Paragraph(f"Industry Insights for Email campaigns for {industry}", section_title))

    try:
        metrics = get_cold_email_kpis(industry)
        if isinstance(metrics, str) and not metrics.startswith("Error"):
            metric_lines = metrics.strip().split('\n')
            for line in metric_lines:
                if not line.strip():
                    continue

                parts = line.split(':**')
                if len(parts) == 2:
                    metric_name = parts[0].replace('1.', '').replace('2.', '').replace('3.', '').replace('**',
                                                                                                         '').strip()
                    value = parts[1].strip()

                    content.append(Paragraph(f"<b>{metric_name}</b>", metrics_header_style))
                    if metric_name == "Open Rate":
                        content.append(Paragraph("The percentage of recipients who open your email", metrics_style))
                    elif metric_name == "Click-Through Rate (CTR)":
                        content.append(
                            Paragraph("The percentage of recipients who click on links in your email", metrics_style))
                    elif metric_name == "Reply Rate":
                        content.append(Paragraph("The percentage of recipients who reply to your email", metrics_style))

                    content.append(Paragraph(f"Industry Average: {value}", metrics_style))

                    try:
                        if "to" in value or "-" in value:
                            content.append(Paragraph("Contact us for a personalized target", metrics_style))
                        else:
                            raw_value = float(value.replace('%', ''))
                            if metric_name == "Open Rate":
                                taippa_target = f"{raw_value * 1.1:.1f}%"
                            elif metric_name == "Click-Through Rate (CTR)":
                                taippa_target = f"{raw_value * 1.3:.1f}%"
                            else:
                                taippa_target = f"{raw_value * 1.5:.1f}%"
                            content.append(Paragraph(f"Taippa Target: {taippa_target}", metrics_style))
                    except ValueError:
                        content.append(Paragraph("Contact us for a personalized target", metrics_style))

                    content.append(Spacer(1, 0.1 * inch))  # Reduced spacing
    except Exception as e:
        print(f"Error processing metrics: {e}")
        content.append(Paragraph("Industry metrics currently unavailable.", body_style))

    # Growth section
    content.append(Paragraph("Accelerate Your Growth with Taippa", section_title))
    growth_text = ("Take your business to the next level with our exclusive strategies "
                   "and tools designed for high-impact growth. Join us for a "
                   "<b>free demo</b> and explore how Taippa can empower your client "
                   "acquisition and revenue acceleration.")
    content.append(Paragraph(growth_text, body_style))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Paragraph("📩 Book Your Free Demo Today!", highlight_style))

    # Create the PDF with reduced margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.5 * inch,  # Reduced from 0.6
        rightMargin=0.5 * inch,  # Reduced from 0.6
        topMargin=0.6 * inch,  # Reduced from 0.8
        bottomMargin=0.5 * inch  # Reduced from 0.6
    )
    doc.build(content, onFirstPage=draw_fancy_background, onLaterPages=draw_fancy_background)
    print(f"PDF generated and saved at {output_path}")
    
def get_image_path():
    try:
        table = airtable_obj(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_CLIENT_TABLE_NAME)
        attachment_column="company_lead_magnet_images"    
        return get_dynamic_images(table,'recHwMDeb62Kgiqx1',attachment_column)
    except Exception as e:
        print(f"Error occured at {__name__} while retrieving the images")

def generate_lead_magnet_pdf(user_id):
    try:
        user_details = collect_information(user_id)
        if user_details is None:
            return "No user details found"
        output_path = "pdf/lead_magnet_personalized.pdf"
        image_path = get_image_path()
        print(f"Image path: {image_path}")
        create_personalized_pdf(user_details,output_path, image_path)
        return {"Status":"Successfull"}
    except Exception as e:
        print(f"Exception occured at {__name__} while generating the lead magnet pdf : {e}")

if __name__=="__main__":
    output_pdf = "lead_magnet_personalized.pdf"
    # user_id for testing
    user_id = "sravan.workemail@gmail.com"
    generate_lead_magnet_pdf(user_id)
    # print(f"PDF generated and saved at {output_pdf}")
    # print("Raw metrics:", metrics)