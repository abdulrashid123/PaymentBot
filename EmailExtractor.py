from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path
from base64 import urlsafe_b64decode, urlsafe_b64encode
import re
from bs4 import BeautifulSoup
from Whmc import WhmcScrapper

class Extractor(WhmcScrapper):
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    UNREAD_PARAMS = {'removeLabelIds': ['UNREAD']}

    def __init__(self,main,report):
        self.main_log = main
        self.report = report
        self.google_pay_emails = []
        self.cash_app_emails =[]
        self.scrapped_email_results = []

    @classmethod
    def loginEmail(cls):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', cls.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    @staticmethod
    def get_params():
        params = {
            "addLabelIds": [
                "Label_5731120152959481311"
            ],
            "removeLabelIds": [
                "INBOX"
            ]
        }
        return params

    def get_all_email(self,service):
        self.main_log.info("fetching cash app emails unread")
        cash_app_emails = service.users().messages().list(userId="me", q="in:inbox from:cash@square.com",maxResults=1000000,
                                        labelIds=['UNREAD']).execute()
        self.cash_app_emails = cash_app_emails.get("messages",[])
        self.main_log.info(f"cash app email count {len(cash_app_emails['messages'])}")
        self.main_log.info("fetching google pay emails unread")
        google_pay_emails = service.users().messages().list(userId="me", q="in:inbox from:googlepay-noreply@google.com",
                                        maxResults=1000000,labelIds=['UNREAD']).execute()
        self.main_log.info(f"google pay email count {len(google_pay_emails.get('messages',[]))}")
        self.google_pay_emails = google_pay_emails.get("messages",[])

    def filter_email(self,service):
        if self.google_pay_emails:
            self.main_log.info("Scrapping and filtering google pay email")
            for each in self.google_pay_emails:
                received = False
                try:
                    id = each["id"]
                    msg = service.users().messages().get(userId='me', id=id, format='full').execute()
                    payload = msg['payload']
                    headers = payload.get("headers")
                    for h in headers:
                        if h["name"].lower() == "subject":
                            print(h)
                            if "received" in h["value"]:
                                received = True
                    parts = payload.get("parts")
                    for part in parts:
                        if part["mimeType"] == "text/html":
                            body = part.get("body")
                            data = body.get("data")
                            text = urlsafe_b64decode(data).decode()
                            soup = BeautifulSoup(text, 'html.parser')
                            invoice_id = soup.find("td", text=re.compile("2012"))
                            transaction_id = soup.find("td", text=re.compile("B."))
                            money_html = soup.findAll("td", text=re.compile("$"))
                            money = None
                            for x in money_html:
                                y = x.get_text(strip=True)
                                if "$" in y:
                                    money_index = y.find("$")
                                    money = y[money_index+1:]
                            if received and invoice_id and transaction_id and money:
                                invoice_id = invoice_id.get_text(strip=True)
                                invoice_id_index = invoice_id.find("2012")
                                invoice_id = invoice_id[invoice_id_index:].replace("”","")
                                transaction_id = transaction_id.get_text(strip=True)
                                email_detail = {"messageId":id,"received":True,"invoiceId":invoice_id,"transaction_id":transaction_id,"money":money}
                                self.scrapped_email_results.append(email_detail)
                            else:
                                print("not valid moved to unable to find")
                                params = self.get_params()
                                service.users().messages().modify(userId='me', id=id,body=params).execute()
                except Exception as e:
                    print("here")
                    print(e)
        else:
            self.main_log.info("No emails found for google pay")

        if self.cash_app_emails:
            self.main_log.info("Scrapping and filtering cash app email")
            for each in self.cash_app_emails:
                try:
                    id = each["id"]
                    msg = service.users().messages().get(userId='me', id=id, format='full').execute()
                    payload = msg['payload']
                    headers = payload.get("headers")
                    for h in headers:
                        if h["name"].lower() == "subject":
                            print(h)
                    parts = payload.get("parts")
                    for part in parts:
                        if part["mimeType"] == "text/html":
                            body = part.get("body")
                            data = body.get("data")
                            text = urlsafe_b64decode(data).decode()
                            soup = BeautifulSoup(text, 'html.parser')
                            received = soup.find("div", text=re.compile("Received"))
                            invoice_id = soup.find("div", text=re.compile("2012"))
                            transaction_id = soup.find("div", text=re.compile("Identifier"))
                            money = soup.findAll("span", text=re.compile("$"))

                            if received and invoice_id and transaction_id and money:
                                received = received.get_text(strip=True)
                                money = money[-1].get_text(strip=True)
                                money_index = money.find("$")
                                money = money[money_index+1:]
                                invoice_id = invoice_id.get_text(strip=True)
                                invoice_id_index = invoice_id.find("2012")
                                invoice_id = invoice_id[invoice_id_index:]
                                transaction_id = transaction_id.findNext("div").get_text(strip=True)
                                email_detail = {"messageId":id,"received":True,"invoiceId":invoice_id,"transaction_id":transaction_id,"money":money}
                                self.scrapped_email_results.append(email_detail)
                            else:
                                print("not valid moved to unable to find")
                                params = self.get_params()
                                service.users().messages().modify(userId='me', id=id,body=params).execute()
                except Exception as e:
                    print(e)
        else:
            self.main_log.info("No emails found for cash app")



    def get_emails_data(self):
        creds = self.loginEmail()
        if creds:
            try:
                self.main_log.info("Logged in Gmail")
                service = build('gmail', 'v1', credentials=creds)
                self.get_all_email(service)
                self.filter_email(service)
                self.add_payment(service)
            except Exception as e:
                print(e)
        else:
            self.main_log.error("Not able to log in")