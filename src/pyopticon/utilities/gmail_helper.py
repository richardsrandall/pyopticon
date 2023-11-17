import smtplib

class GmailHelper:
       """ This widget allows your Python code to send emails and, by extension, texts. It's mainly useful for sending notifications after an interlock is 
       tripped, e.g. if the dashboard detects that an instrument went offline partway through an automation script.\n
       
       You'll need to follow an online tutorial to get an 'app password' for a gmail account to allow Python to send emails from that account. 
       You can test that it worked by constructing a GmailHelper object in a shell like IDLE and trying to send yourself emails from it. 
       If you'd like to send texts, send an email to the appropriate address at the cell carrier's SMS gateway, e.g. xxx-xxx-xxxx@vtext.com for Verizon. 

       :param gmail_address: The gmail address from which you want the notification to be sent.
       :type gmail_address: str
       :param auth_string: An app password (or equivalent) for the gmail account.
       :type auth_string: str
       :param destination_emails: A list of the email addresses to which you want to send the notifications.
       :type destination_emails: str

       """

       def __init__(self, gmail_address, auth_string, destination_emails):
              """The constructor for a GmailHelper object"""
              self.gmail_address = gmail_address
              self.auth_string = auth_string
              self.destinations = destination_emails

       def send_email(self, subject, message_body):
              """Send an email with the specified subject and message to the email addresses specified when this GmailHelper was created.
              
              :param subject: The subject of the email. Note that if you're using this to send texts through an SMS gateway, different carriers treat the subject in different ways.
              :type subject: str
              :param message_body: The body text of the email message to send.
              :type message_body: str
              """
              try:
                # Authentication for the gmail account
                auth = (self.gmail_address, self.auth_string)              
                # Establish a secure session with gmail's outgoing SMTP server using your gmail account
                server = smtplib.SMTP( "smtp.gmail.com", 587 )
                server.starttls()
                server.login(auth[0], auth[1])
                # Send the messages
                message = 'Subject: {}\n\n{}'.format(subject, message_body)
                for destination in self.destinations:
                        server.sendmail( auth[0], str(destination), message)
              except Exception as e:
                print("Email failed, error: "+str(e))