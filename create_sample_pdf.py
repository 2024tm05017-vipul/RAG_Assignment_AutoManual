"""Generate sample automotive service manual PDF for testing"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from datetime import datetime
import io


def create_sample_pdf():
    """Create a sample engine service manual PDF"""
    
    filename = "sample_documents/engine_service_manual.pdf"
    
    # Create PDF
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch,
        title="Engine Service Manual - Quality Control Edition"
    )
    
    # Container for PDF elements
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#003366'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#003366'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    body_style = styles['BodyText']
    body_style.fontSize = 10
    body_style.leading = 14
    
    # Title
    elements.append(Paragraph("ENGINE SERVICE MANUAL", title_style))
    elements.append(Paragraph("Quality Control & Diagnostic Guide", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Document info
    info_text = f"""
    <b>Document ID:</b> ESM-2024-V6<br/>
    <b>Revision:</b> G<br/>
    <b>Date:</b> {datetime.now().strftime('%B %d, %Y')}<br/>
    <b>Domain:</b> Automotive Manufacturing Quality Control<br/>
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Section 1: Introduction
    elements.append(Paragraph("1. ENGINE SPECIFICATIONS", heading_style))
    elements.append(Paragraph(
        """This service manual provides comprehensive specifications for quality control 
        of automotive engines. It includes torque specifications, temperature limits, pressure ranges,
        and diagnostic procedures for V4, V6, and V8 engine variants.""",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Section 2: Torque Specifications Table
    elements.append(Paragraph("2. TORQUE SPECIFICATIONS", heading_style))
    elements.append(Paragraph(
        """All bolts and fasteners must be torqued to specification. Failure to follow these 
        specifications may result in component failure, leakage, or safety hazards.""",
        body_style
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    # Torque table
    torque_data = [
        ['Component', 'V4 Engine\n(2.0L)', 'V6 Engine\n(2.5L)', 'V8 Engine\n(3.6L)', 'Unit', 'Safety Note'],
        ['Intake Manifold Bolts', '25±2', '28±2', '32±2', 'Nm', 'Multi-stage tightening'],
        ['Cylinder Head Bolts', '85±5', '95±5', '110±5', 'Nm', 'Follow sequence'],
        ['Oil Pan Bolts', '18±1', '20±1', '24±1', 'Nm', 'Small bolts only'],
        ['Spark Plug', '18±2', '18±2', '18±2', 'Nm', 'Gap: 0.035-0.045 in'],
        ['Alternator Mount', '35±3', '40±3', '45±3', 'Nm', 'Use thread locker'],
        ['Engine Mount Bolts', '65±5', '70±5', '80±5', 'Nm', 'Must be final step'],
        ['Transmission Bell', '45±3', '50±3', '55±3', 'Nm', 'Alignment check required'],
    ]
    
    table = Table(torque_data, colWidths=[1.2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.5*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Section 3: Temperature Specifications
    elements.append(Paragraph("3. ENGINE TEMPERATURE SPECIFICATIONS", heading_style))
    elements.append(Paragraph(
        """Temperature monitoring is critical for engine health. The following table provides 
        nominal and limit values for different engine variants during standard operation.""",
        body_style
    ))
    elements.append(Spacer(1, 0.15*inch))
    
    temp_data = [
        ['Parameter', 'V4\n(°C)', 'V6\n(°C)', 'V8\n(°C)', 'Nominal', 'Upper Limit', 'Critical'],
        ['Coolant Temperature', '80-90', '85-95', '90-100', '90°C', '110°C', '115°C'],
        ['Oil Temperature', '85-100', '90-105', '95-110', '100°C', '120°C', '135°C'],
        ['EGR Temperature', '200-220', '210-230', '220-240', '220°C', '250°C', '280°C'],
        ['Turbo Outlet (if equipped)', '450-550', '480-580', '500-600', '550°C', '650°C', '700°C'],
    ]
    
    temp_table = Table(temp_data, colWidths=[1.4*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.7*inch])
    temp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006600')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightcyan]),
    ]))
    elements.append(temp_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Page break before section 4
    elements.append(PageBreak())
    
    # Section 4: Diagnostic Flowchart (as text, will reference an image slot)
    elements.append(Paragraph("4. DIAGNOSTIC PROCEDURE - LEAN COMBUSTION ANOMALY", heading_style))
    elements.append(Paragraph(
        """<b><u>Engine Warning Light Troubleshooting</u></b><br/><br/>
        When the engine control module (ECM) detects a lean combustion condition 
        (air-fuel ratio >14.7:1), the following diagnostic steps must be followed:<br/><br/>
        <b>Step 1: Initial Inspection</b><br/>
        • Check fuel pressure regulator vacuum line<br/>
        • Inspect O2 sensor wiring for damage<br/>
        • Verify fuel injector resistance (11-15Ω expected)<br/><br/>
        <b>Step 2: Pressure Tests</b><br/>
        • Measure fuel rail pressure (35-45 PSI normal)<br/>
        • Perform fuel injector flow test<br/>
        • Check fuel filter restriction<br/><br/>
        <b>Step 3: Sensor Diagnostics</b><br/>
        • Upstream O2 sensor signal (0.4-0.8V nominal)<br/>
        • Downstream O2 sensor signal (0.2-0.8V nominal)<br/>
        • Mass air flow (MAF) sensor output<br/><br/>
        <b>Step 4: Resolution</b><br/>
        • If fuel pressure low → Replace fuel pump or filter<br/>
        • If O2 sensor faulty → Replace sensor<br/>
        • If injector resistance high → Replace injector<br/>""",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    # Section 5: Quality Control Checklist
    elements.append(Paragraph("5. QUALITY CONTROL CHECKLIST", heading_style))
    
    checklist_data = [
        ['No.', 'Item', 'Reference', 'Status', 'Notes'],
        ['1', 'Intake manifold torque verification', 'Section 2, Row 1', '□ Pass / □ Fail', ''],
        ['2', 'Spark plug gap measurement', 'Section 2, Row 4', '□ Pass / □ Fail', 'Use 0.040 in gauge'],
        ['3', 'Coolant temperature sensor function', 'Section 3, Row 1', '□ Pass / □ Fail', ''],
        ['4', 'Fuel injector electrical resistance', 'Section 4, Step 2', '□ Pass / □ Fail', 'Expected: 11-15Ω'],
        ['5', 'O2 sensor signal voltage', 'Section 4, Step 3', '□ Pass / □ Fail', 'Upstream: 0.4-0.8V'],
        ['6', 'Engine mount bolt tightness', 'Section 2, Row 7', '□ Pass / □ Fail', 'Use torque wrench'],
    ]
    
    checklist = Table(checklist_data, colWidths=[0.4*inch, 1.8*inch, 1.2*inch, 0.8*inch, 1.6*inch])
    checklist.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#660000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightblue]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(checklist)
    elements.append(Spacer(1, 0.3*inch))
    
    # Section 6: Safety Warnings
    elements.append(Paragraph("6. SAFETY WARNINGS", heading_style))
    elements.append(Paragraph(
        """<b>⚠ CRITICAL SAFETY INFORMATION</b><br/>
        • Never work on hot engines. Allow 15 minutes cooling time.<br/>
        • Properly relieve fuel system pressure before disconnecting fuel lines.<br/>
        • Wear safety glasses and gloves when working with chemicals.<br/>
        • Use OEM-approved parts for all replacements - counterfeit parts cause 40% of QC failures.<br/>
        • Torque all fasteners in sequence as specified - improper torque causes gasket failure.<br/>
        • Test all electrical connections for proper voltage before assembly.<br/>
        • Document all deviations from specification in QC report form.<br/><br/>
        <i>Failure to follow these procedures may result in component damage, 
        warranty claims, or safety hazards.</i>""",
        body_style
    ))
    elements.append(Spacer(1, 0.4*inch))
    
    # Footer
    elements.append(Paragraph(
        "This manual contains confidential proprietary information. " +
        "Unauthorized distribution is prohibited.",
        styles['Italic']
    ))
    
    # Build PDF
    doc.build(elements)
    print(f"✓ Sample PDF created: {filename}")
    return filename


if __name__ == "__main__":
    try:
        create_sample_pdf()
    except ImportError as e:
        print(f"Error: {e}")
        print("Install reportlab: pip install reportlab")
