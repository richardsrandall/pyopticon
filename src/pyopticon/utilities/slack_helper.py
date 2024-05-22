import requests
import json

class SlackHelper:
        """ This widget allows your Python code to send messages to a Slack webhook. It's mainly useful for sending notifications after an interlock is 
        tripped, e.g. if the dashboard detects that an instrument went offline partway through an automation script.\n
       
        You'll need to follow an online tutorial to get a webhook URL from Slack for the channel you want to post in. 

        :param webhook_url: The Webhook URL provided by Slack to for sending a message to a channel.
        :type webhook_url: str

       """

        def __init__(self, webhook_url):
              """The constructor for a SlackHelper object"""
              self.webhook_url = webhook_url

        def send_message(self, message_body):
              """Send a Slack message to the webhook used when this helper was created.
              
              :param message_body: The text of the message to send.
              :type message_body: str
              """
              try:
                payload = {"text": message_body}
                r = requests.post(self.webhook_url, json=payload)

              except Exception as e:
                print("Slack webhook failed, error: "+str(e))