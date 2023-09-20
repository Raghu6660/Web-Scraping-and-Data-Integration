import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import csv
import zipfile
import urllib.parse

import smtplib  
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

url = 'https://www.laptopsdirect.co.uk/ct/laptops-and-netbooks/laptops?fts=laptops' # This is the e-commerce website link 

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

results = soup.find_all('div', {'class':'OfferBox'})

products = []
root_url = 'https://www.laptopsdirect.co.uk/'

# Targting the requried data from html 

for item in results:
    name=""
    price=0
    rate=0
    comb_url=""
    pro_det=""
     # name
    try:
        name = item.find('a', {'class':'offerboxtitle'}).get_text() 
    except:
        name = 'n/a'
    
    # price
    try:
        price = item.find('span', {'class':'offerprice'}).get_text()
    except:
        price = 'n/a'
    
    # review rating
    try:
        rate = item.find('span').get_text()
    except:
        rate = 'n/a'
        
    # relative URL
    try:
        ref_url = item.find('a', {'class':'offerboxtitle'}).get('href')
        comb_url = urllib.parse.urljoin(root_url, ref_url)
    except:
        comb_url = 'n/a'
    
    #product details
    try:
        pro_det = item.find('div', {'class':'productInfo'}).get_text().strip().replace('\n',', ')
    except:
        pro_det = 'n/a'
    
    
    products.append({
        'name' : name,
        'price' : price.strip(),
        'rating' : rate,
        'urls' : comb_url,
        'details' : pro_det
    })
    
# Connecting to mongoDB and inserting the scraped data
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['ecommerce_db']
    collection = db['products']
    collection.insert_many(products)

    client.close()
except:
    print("Problem raised entring the data in database")

# Making scraped data into csv file

try:
    with open('scraped_products.csv', 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = products[0].keys() #['name', 'price', 'rating', 'urls', 'details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for product in products:
            writer.writerow(product)
except:
    print("Problem raised in making data file")

# Zipping the grendrated file

with zipfile.ZipFile('scraped_products.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
    zipf.write('scraped_products.csv')

# Seking the email credentials for sending file

senderemail = input("Enter your email to send zip file-------")
senderpassword = input("Enter your password------")
reciveremail = input("Enter Reciver email to send zip file-------")

from_email = senderemail 
to_email = reciveremail 
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = senderemail
smtp_password = senderpassword 


message = MIMEMultipart()
message['From'] = from_email
message['To'] = to_email
message['Subject'] = "Scraped Products Data"

with open("scraped_products.zip", "rb") as attachment:
    part = MIMEBase("application", "octet-stream")
    part.set_payload(attachment.read())


encoders.encode_base64(part)
part.add_header(
    "Content-Disposition",
    f"attachment; filename=scraped_products.zip",
)
message.attach(part)

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
try:
    server.login(smtp_username, smtp_password)
except:
    print("Can not Login, Please Try again!")

try:
    server.sendmail(from_email, to_email, message.as_string())
except:
    print("Something went wrong! Email haven't sent")

print("EMAIL SENT SUCCESSFULY")

server.quit()