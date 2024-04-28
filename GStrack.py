import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from email.message import EmailMessage
import ssl
import smtplib
from email.utils import formataddr
import os
from pathlib import Path
from dotenv import load_dotenv

sender : st.secrets["SENDER"]
password : st.secrets["PASSWORD"]
receiver : st.secrets["RECEIVER"]
subject = 'carbon offset update notice'


#page title
st.title("Recording your carbon offset contributions")
st.markdown("Please enter the relevant details of the emissions reduced")

#link to google sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing vendors data
existing_data = conn.read(worksheet="Vendors", usecols=list(range(10)), ttl=5)
existing_data = existing_data.dropna(how="all")  

#List of Business Types
Business_types = [
    "Manufacturer",
    "Distributor",
    "Wholesaler",
    "Retailer",
    "Service Provider",
]
PRODUCTS = [
    "Bamboo inserts",
    "Diapers",
    "Shipping",
    "Other",
]

#form
with st.form(key="vendor_form"):
    company_name = st.text_input(label="Company Name*",placeholder="Please write down the full name of your company")
    Contact = st.text_input(label="Name of person in charge*", placeholder="Please input the name of the person in charge")
    business_type = st.selectbox("Which part of our operations does your company assist with?*", options=Business_types, index=None)
    products = st.multiselect("What specific product(s) does your company provide?*", options=PRODUCTS)
    buyer_email = st.text_input("Email*", placeholder="Your company's email address")
    product_quantity = st.text_input("Quantity of the product that was manufactured*", placeholder="Quantity of the product produced")
    emission_reduction = st.text_input("Quantity(in metric tonnes) of greenhouse gas emissions reduced*",placeholder="Quantity reduced (in metric tonnes)")
    audit_firm = st.text_input(label="Auditing firm*",placeholder="The firm that had audited the claim for greenhouse gas emissions")
    audit_email = st.text_input(label="Email of auditing firm*", placeholder="please type down the full email address")
    date = st.date_input(label="Date of submission (Today's date)*")

#Mark required fields
    st.markdown("**required*")
    submit_button = st.form_submit_button(label="Submit Details")


#necessary checks to ensure that all required fields are filled
    if submit_button:
        if not company_name or not Contact or not business_type or not products or not buyer_email or not product_quantity or not emission_reduction or not audit_firm or not audit_email or not date:
            st.warning("Ensure all mandatory fields are filled.")
            st.stop()
        else:
            vendor_data = pd.DataFrame(
                    [
                        {
                            "CompanyName": company_name,
                            "Point of contact" : Contact, 
                            "BusinessType": business_type,
                            "Products": ", ".join(products),
                            "Email": buyer_email,
                            "Quantity": product_quantity,
                            "Emission reduction" : emission_reduction, 
                            "Auditing agency" : audit_firm,
                            "Contact" : audit_email, 
                            "Date": date.strftime("%Y-%m-%d"),
                        }
                    ]
                )
        #Adding the above info to the existing data
        updated_df = pd.concat([existing_data, vendor_data], ignore_index=True)
        conn.update(worksheet="Vendors", data=updated_df)
        st.success("Your emission reduction update has been successfully submitted!")
        
        #email
        body = f"""
        {company_name} of {buyer_email} has provided an update that as of {date},the company has reduced {emission_reduction} metric tonnes of greenhouse gas.
        The company produces {product_quantity} of {products}. Please view the details at https://docs.google.com/spreadsheets/d/1nkTlHniZb2Rcp_mr9Z8YQENdrqkjF8BfmuSkfbXmm1Q
        """
        em = EmailMessage()
        em['From'] = formataddr(("Francois G.D.", sender))
        em['To'] = receiver
        em['subject'] = subject
        em.set_content(body)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
        sent = True

#Email to request for verification
        body = f"""
        Hi,
        I am a representative of Comfybums and the firm {company_name} has provided an update that as of {date},the company has reduced {emission_reduction} metric tonnes of greenhouse gas
        through the production of {product_quantity} of {products}. As a part of their update, they have listed your firm as the auditing agency. 
        With that in mind, we would like to request for a copy of the auditing report in order to verify the claim. Thank you for your assistance.
        
        Best Regards,
        Comfybums
        """
        em = EmailMessage()
        em['From'] = formataddr(("Francois G.D.", sender))
        em['To'] = audit_email
        em['subject'] = "request for audit report"
        em.set_content(body)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
        sent = True
        


    



