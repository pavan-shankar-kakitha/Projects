import smtplib
import ssl
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 
SENDER_EMAIL = "facialattendancesystem@gmail.com"
SENDER_PASSWORD = "qejf gzva iinu ayld"  

def send_attendance_email(parent_email, student_name, status, date_str, time_str):
    subject = f"Attendance Update for {student_name} - {date_str}"
    body = (
        f"Dear Parent,\n\n"
        f"This is an automated message from the Facial Recognition Attendance System.\n"
        f"Attendance details of your child are below:\n\n"
        f"Student Name : {student_name}\n"
        f"Date         : {date_str}\n"
        f"Time         : {time_str}\n"
        f"Status       : {status}\n\n"
        f"Regards,\nAttendance Office"
    )

    msg = EmailMessage()
    msg["From"] = SENDER_EMAIL
    msg["To"] = parent_email
    msg["Subject"] = subject
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
