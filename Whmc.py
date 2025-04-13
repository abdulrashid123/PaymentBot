from twocaptcha import TwoCaptcha
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
class WhmcScrapper():
    URL = "https://thenexthosting.com/thenextadmin/index.php"
    username = "payment@1809"
    password = "Pay@qqzbofjj8SZg!$"
    solver = TwoCaptcha('05273152359ea160d6fa301343e432c5')

    def initialize(self):
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument('log-level=3')
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options,service=service)
        self.driver.implicitly_wait(10)
        self.driver.get(self.URL)
        self.login()

    def page_has_loaded(self):
        page_state = self.driver.execute_script('return document.readyState;')
        if page_state == 'complete':
            self.main_log.info("Page Loaded")
        else:
            time.sleep(1)
            self.page_has_loaded()

    def fill_captcha(self):
        result = self.solver.normal('image.png')
        captcha_input = self.driver.find_element_by_id('inputCaptcha')
        code = result.get('code')
        self.main_log.info(f"Captcha found {code}")
        captcha_input.send_keys(code.upper())

    def login(self):
        self.driver.find_element(By.ID, 'inputCaptchaImage').screenshot('image.png')
        username = self.driver.find_element_by_xpath('//input[@name="username"]')
        password = self.driver.find_element_by_xpath('//input[@name="password"]')
        self.fill_captcha()
        username.send_keys(self.username)
        password.send_keys(self.password)
        button = self.driver.find_element_by_xpath('//input[@value="Login"]')
        self.driver.execute_script("arguments[0].click()", button)
        try:
            self.driver.find_element_by_xpath('//a[@href="/thenextadmin/orders.php?status=Pending"]')
        except:
            self.main_log.exception("Logged In Error", exc_info=True)
            self.login()

    @staticmethod
    def validate(each):
        pass

    def add_payment(self,service):
        try:
            self.initialize()
        except:
            self.main_log.exception("Intialization Error", exc_info=True)
            raise Exception("Intialization error")
        self.main_log.info("Payment adding started")
        print(len(self.scrapped_email_results))
        for each in self.scrapped_email_results:
            print(each)
            try:
                invoiceId = each["invoiceId"]
                money = each["money"]
                transaction_id = each.get("transaction_id",None)
                messageId = each["messageId"]
                url = f"https://thenexthosting.com/thenextadmin/invoices.php?action=edit&id={invoiceId}#tab=2"
                self.driver.get(url)
                soup = BeautifulSoup(self.driver.page_source,'html.parser')
                error = soup.find("p",text="Error: Invalid invoice id provided")
                invoice_paid = soup.find("span",text="Invoice in Paid Status")
                if not error and not invoice_paid:
                    ne = False
                    trans_ele = self.driver.find_element_by_name("transid")
                    money_ele = self.driver.find_element_by_name("amount")
                    amount_text = self.driver.find_element_by_name("amount").text
                    if amount_text:
                        try:
                            amount = float(amount_text)
                            print(amount,money)
                            if amount != float(money):
                                ne = True
                                params = self.get_params()
                                service.users().messages().modify(userId='me', id=messageId, body=params).execute()
                        except Exception as e:
                            print(e)

                    trans_ele.clear()
                    money_ele.clear()
                    if transaction_id:
                        trans_ele.send_keys(transaction_id)
                    money_ele.send_keys(money)
                    button = self.driver.find_element_by_id("paymentText")
                    self.driver.execute_script("arguments[0].click()",button)
                    success = self.driver.find_elements_by_class_name("textred")
                    time.sleep(3)
                    print(success,ne)
                    if success and not ne:
                        self.main_log.info(f"found {invoiceId} {messageId} {transaction_id} adding to READ")
                        self.report.info(f"found {invoiceId} {messageId} {transaction_id} adding to READ")
                        params = self.UNREAD_PARAMS
                        service.users().messages().modify(userId='me', id=messageId, body=params).execute()

                else:
                    if invoice_paid:
                        self.main_log.info(f"found {invoiceId} {messageId} {transaction_id} adding to READ")
                        self.report.info(f"Invoice already paid")
                        params = self.UNREAD_PARAMS
                        service.users().messages().modify(userId='me', id=messageId, body=params).execute()
                    else:
                        service.users().messages().modify(userId='me', id=messageId, body=params).execute()
                        self.main_log.info(f"Not found {invoiceId} {messageId} {transaction_id} adding to unable to find")
                        params = self.get_params()
                        service.users().messages().modify(userId='me', id=messageId, body=params).execute()
            except Exception as e:
                print(e)
        if self.driver:
            self.driver.quit()
        self.main_log.info("driver closed task completed")
