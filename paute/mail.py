import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def send(subject, body, attachment_file, sender, password):
    # Users to send email
    recipients = [
        "ccardenas@inamhi.gob.ec",
        "angelica.gutierrez@noaa.gov",
        "secretariat@geoglows.org",
        "vanesa.martin@nasa.gov",
        "rodrigotorres@ecociencia.org",
        "jusethchancay@ecociencia.org"]
    #
    # SMTP server
    smtp_server = "smtp.office365.com"
    smtp_port = 587
    #
    # Configure the message
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ", ".join(recipients)
    message['Subject'] = subject
    #
    # Attach the email body
    message.attach(MIMEText(body, 'plain'))
    #
    # Attach the PDF file
    attachment = open(attachment_file, 'rb')
    attachment_part = MIMEBase('application', 'octet-stream')
    attachment_part.set_payload((attachment).read())
    encoders.encode_base64(attachment_part)
    attachment_part.add_header('Content-Disposition', "attachment; filename= %s" % attachment_file)
    message.attach(attachment_part)
    #
    # Connect to the SMTP server and send the email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender, password)
    server.sendmail(sender, recipients, message.as_string())
    server.quit()


