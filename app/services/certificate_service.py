import io
from datetime import date
from typing import Optional, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from app.core.logging import logger


class CertificateGenerationError(Exception):
    """Raised when PDF certificate generation fails."""
    pass


class CertificateService:
    """Service responsible for generating professional PDF certificates using ReportLab."""

    @staticmethod
    def _draw_decorations(c: canvas.Canvas, width: float, height: float) -> None:
        """Draw professional borders, ribbons, and vector seals."""
        # Primary Outer Navy Border
        c.setStrokeColor(colors.HexColor("#1A365D"))  # Deep Navy
        c.setLineWidth(6)
        c.rect(20, 20, width - 40, height - 40)

        # Secondary Inner Gold Border
        c.setStrokeColor(colors.HexColor("#D69E2E"))  # Warm Gold
        c.setLineWidth(2)
        c.rect(28, 28, width - 56, height - 56)

        # Corner Accents (Gold corner brackets)
        accent_len = 30
        c.setLineWidth(3)
        c.setStrokeColor(colors.HexColor("#B7791F"))
        for x, y, dx, dy in [
            (35, 35, accent_len, accent_len),
            (width - 35, 35, -accent_len, accent_len),
            (35, height - 35, accent_len, -accent_len),
            (width - 35, height - 35, -accent_len, -accent_len),
        ]:
            c.line(x, y, x + dx, y)
            c.line(x, y, x, y + dy)

        # Gold Seal / Rosette in bottom-right area
        seal_x = width - 110
        seal_y = 90
        seal_r = 32

        # Draw outer scalloped/cog circle
        c.setFillColor(colors.HexColor("#D69E2E"))
        c.circle(seal_x, seal_y, seal_r, stroke=0, fill=1)

        # Draw inner gold-dark circle
        c.setFillColor(colors.HexColor("#B7791F"))
        c.circle(seal_x, seal_y, seal_r - 4, stroke=0, fill=1)

        # Draw central white circle
        c.setFillColor(colors.HexColor("#1A365D"))
        c.circle(seal_x, seal_y, seal_r - 7, stroke=0, fill=1)

        # Text inside seal
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(seal_x, seal_y + 4, "OFFICIAL")
        c.drawCentredString(seal_x, seal_y - 6, "VERIFIED")

        # Ribbon tails hanging from seal
        c.setFillColor(colors.HexColor("#975A16"))
        p = c.beginPath()
        p.moveTo(seal_x - 14, seal_y - 20)
        p.lineTo(seal_x - 22, seal_y - 55)
        p.lineTo(seal_x - 10, seal_y - 48)
        p.lineTo(seal_x, seal_y - 55)
        p.lineTo(seal_x + 10, seal_y - 48)
        p.lineTo(seal_x + 22, seal_y - 55)
        p.lineTo(seal_x + 14, seal_y - 20)
        p.close()
        c.drawPath(p, fill=1, stroke=0)

    @classmethod
    def generate_pdf(
        cls,
        certificate_id: str,
        recipient_name: str,
        title: str,
        course_name: str,
        issuer_name: str,
        issue_date: date,
        custom_attributes: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generates a high-quality certificate PDF in-memory and returns bytes.
        """
        # Intentional failure trigger for testing failure isolation:
        # If recipient name starts with '__SIMULATE_FAILURE__', raise error.
        if recipient_name.startswith("__SIMULATE_FAILURE__"):
            raise CertificateGenerationError(
                f"Simulated generation failure for recipient: {recipient_name}"
            )

        try:
            buffer = io.BytesIO()
            page_width, page_height = landscape(A4)
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
            c.setTitle(f"{title} - {recipient_name}")
            c.setAuthor(issuer_name)
            c.setSubject(course_name)

            # Draw decorative borders and seal
            cls._draw_decorations(c, page_width, page_height)

            # Issuer / Organization Name Header
            c.setFillColor(colors.HexColor("#2D3748"))
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(page_width / 2.0, page_height - 75, issuer_name.upper())

            # Subtle accent line under issuer
            c.setStrokeColor(colors.HexColor("#CBD5E0"))
            c.setLineWidth(1)
            c.line(page_width / 2.0 - 150, page_height - 85, page_width / 2.0 + 150, page_height - 85)

            # Certificate Title
            c.setFillColor(colors.HexColor("#1A365D"))
            c.setFont("Helvetica-Bold", 30)
            c.drawCentredString(page_width / 2.0, page_height - 130, title.upper())

            # Presentation Subtitle
            c.setFillColor(colors.HexColor("#718096"))
            c.setFont("Helvetica-Oblique", 14)
            c.drawCentredString(page_width / 2.0, page_height - 170, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

            # Recipient Name with dynamic font-size scaling
            c.setFillColor(colors.HexColor("#2C5282"))
            name_len = len(recipient_name)
            if name_len > 35:
                name_font_size = 24
            elif name_len > 25:
                name_font_size = 28
            else:
                name_font_size = 36

            c.setFont("Helvetica-Bold", name_font_size)
            c.drawCentredString(page_width / 2.0, page_height - 225, recipient_name)

            # Name underline
            name_width = c.stringWidth(recipient_name, "Helvetica-Bold", name_font_size)
            underline_width = max(name_width + 40, 260)
            c.setStrokeColor(colors.HexColor("#D69E2E"))
            c.setLineWidth(2)
            c.line(
                page_width / 2.0 - underline_width / 2.0,
                page_height - 235,
                page_width / 2.0 + underline_width / 2.0,
                page_height - 235,
            )

            # Completion description
            c.setFillColor(colors.HexColor("#4A5568"))
            c.setFont("Helvetica", 13)
            c.drawCentredString(
                page_width / 2.0,
                page_height - 275,
                "for outstanding performance and successful completion of the course",
            )

            # Course / Event Name
            c.setFillColor(colors.HexColor("#1A202C"))
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(page_width / 2.0, page_height - 310, course_name)

            # Optional custom attributes display (e.g. honors, grade, duration)
            if custom_attributes:
                extras = []
                for k, v in custom_attributes.items():
                    if isinstance(v, (str, int, float)):
                        extras.append(f"{k.replace('_', ' ').capitalize()}: {v}")
                if extras:
                    extra_text = " • ".join(extras[:3])
                    c.setFillColor(colors.HexColor("#718096"))
                    c.setFont("Helvetica-Oblique", 11)
                    c.drawCentredString(page_width / 2.0, page_height - 335, extra_text)

            # Signatures & Footer metadata
            c.setFont("Helvetica", 10)
            c.setFillColor(colors.HexColor("#4A5568"))

            # Left block: Date of issue & Certificate Verification ID
            formatted_date = issue_date.strftime("%B %d, %Y")
            c.drawString(70, 110, f"Date Issued: {formatted_date}")
            c.drawString(70, 92, f"Certificate ID: {certificate_id}")
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(70, 76, "Verify authenticity via verification ID")

            # Center-Right: Signature line
            c.setStrokeColor(colors.HexColor("#4A5568"))
            c.setLineWidth(1)
            sig_x = page_width / 2.0 + 80
            c.line(sig_x - 70, 105, sig_x + 90, 105)

            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(colors.HexColor("#2D3748"))
            c.drawCentredString(sig_x + 10, 90, "Authorized Program Director")
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.HexColor("#718096"))
            c.drawCentredString(sig_x + 10, 76, issuer_name)

            c.showPage()
            c.save()

            buffer.seek(0)
            pdf_bytes = buffer.getvalue()
            return pdf_bytes

        except Exception as e:
            if isinstance(e, CertificateGenerationError):
                raise
            logger.error("Error generating certificate %s: %s", certificate_id, str(e), exc_info=True)
            raise CertificateGenerationError(f"Failed to generate certificate PDF: {str(e)}") from e


certificate_service = CertificateService()
