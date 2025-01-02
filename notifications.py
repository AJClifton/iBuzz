import smtplib


class Notifications:
    from_email = "ibuzz2notifications@gmail.com"

    def __init__(self, gmail, password):
        self.from_email = gmail
        self.smtp = smtplib.SMTP('smtp.gmail.com', 587)
        self.smtp.starttls()
        self.smtp.login(self.from_email, password)
        #self.smtp.login(self.from_email, "aqvg jxxj prif ggca")


    def send_email_notification(self, recipient, subject, message):
        """Send an email to the given recipient.
        
        :param str recipient: recipient's email address"""
        email = f"""From: {self.from_email}\nTo: {recipient}\nSubject: {subject}\n\n{message}"""
        self.smtp.sendmail(self.from_email, recipient, email)