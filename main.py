import streamlit as st
from dotenv import load_dotenv
import requests
import json
import os

import ntpath #Get the File Path
import base64 #Convert Files for posting
import mimetypes #Get the content Type

from PIL import Image

# setup streamlit page
st.set_page_config(
	page_title="DAW-AI",
	page_icon="💊"
)
st.header("DAW-AI")
st.subheader("One stop solution for all medicine data")

load_dotenv()
# Define the base URL and other properties
base_url = os.getenv("base_url")
tenant_id = os.getenv("tenant_id")
username = os.getenv("username")
password = os.getenv("password")
client_id = os.getenv("client_id")
client_secret =  os.getenv("client_secret")

@st.cache_data
def load_image(image_file):
	img = Image.open(image_file)
	return img

@st.cache_data
def get_token():
	# Construct the token URL
	token_url = f"{base_url}/tenants/{tenant_id}/oauth2/token"

	# Create the headers and payload for the request
	headers = {
		'Content-Type': 'application/json',
	}

	payload = {
		'client_id': client_id,
		'client_secret': client_secret,
		'grant_type': 'password',
		'username': username,
		'password': password
	}

	access_token = None

	# Make the POST request to get the access token
	try:
		response = requests.post(token_url, headers=headers, data=json.dumps(payload))
		response.raise_for_status()
		data = response.json()
		access_token = data['access_token']
		print(f"Access Token: {access_token}")
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")

	return access_token

access_token_state = st.text('Loading token...')
access_token = get_token()
access_token_state.text("Opentext token loaded now")

st.subheader('Load the image of your bill')

import requests

image_file = st.file_uploader("Choose a image file", type="jpeg")
if image_file is not None:
	file_details = {"FileName":image_file.name,"FileType":image_file.type}
	st.write(file_details)
	img = load_image(image_file)
	st.image(img)
	with open(os.path.join("/tmp","image.jpeg"),"wb") as f:
		f.write(image_file.getbuffer())         
	st.success("Saved File")

	st.subheader("Medicine Details")

	# Define the base URL and other properties
	file_path = "/tmp/image.jpeg"  # Replace with the actual file path
	file_type = "image/jpeg"  # Replace with the appropriate content type
	file_length = os.path.getsize(file_path)

	# Construct the URL for file upload
	upload_url = f"{base_url}/capture/cp-rest/v2/session/files"

	# Set the headers for the request
	headers = {
		'Authorization': f'Bearer {access_token}',
		'Accept': 'application/hal+json',
		'Accept-Language': 'en-US',
		'Content-Type': file_type,
		'Content-Length': str(file_length)
	}

	# Open and read the file
	with open(file_path, 'rb') as file:
		file_content = file.read()

	captured_file_id = None
	# Make the POST request to upload the file
	try:
		response = requests.post(upload_url, headers=headers, data=file_content)
		response.raise_for_status()
		data = response.json()
		captured_file_id = data['id']
		print(f"Captured File ID: {captured_file_id}")
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")


	# Define the base URL and other properties
	file_type = "application/hal+json"  # Replace with the appropriate content type

	# Define the PDF file name and captured file ID (replace with actual values)
	pdf_file_name = ntpath.basename(file_path)

	# Construct the URL for creating a searchable PDF
	pdf_creation_url = f"{base_url}/capture/cp-rest/v2/session/services/fullpageocr"

	# Set the headers and payload for the request
	headers = {
		'Authorization': f'Bearer {access_token}',
		'Accept': 'application/hal+json',
		'Accept-Language': 'en-US',
		'Content-Type': file_type,
	}

	# Construct the request payload as a Python dictionary
	request_payload = {
		"serviceProps": [
			{"name": "Env", "value": "D"},
			{"name": "OcrEngineName", "value": "Advanced"},
			{"name":"AutoRotate", "value":"True"}
		],
		"requestItems": [
			{
				"nodeId": 1,
				"values": [{"name": "OutputType", "value": "pdf"}],
				"files": [
					{
						"name": pdf_file_name,
						"value": captured_file_id,
						"contentType": file_type
					}
				]
			}
		]
	}

	ocr_response_data = None
	# Make the POST request to create a searchable PDF
	try:
		response = requests.post(pdf_creation_url, headers=headers, data=json.dumps(request_payload))
		response.raise_for_status()
		ocr_response_data = response.json()
		print(ocr_response_data)
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")

	# Construct the URL to retrieve the file
	if ocr_response_data['resultItems'] is not None and len(ocr_response_data['resultItems'])>0 and 'files' in ocr_response_data['resultItems'][0] and len(ocr_response_data['resultItems'][0]['files']) > 0:
		retrieve_url = ocr_response_data['resultItems'][0]['files'][0]['src']
	else:
		st.write("NO PDF generated")
		exit()

	# Set the headers for the GET request
	headers = {
		'Accept-Language': 'en-US',
		'Authorization': f'Bearer {access_token}'
	}

	# Make the GET request to retrieve the file
	try:
		response = requests.get(retrieve_url, headers=headers)
		response.raise_for_status()

		# You can handle the response here as needed
		# For example, if you want to save the response content to a file:
		with open("output.pdf", "wb") as pdf_file:
			pdf_file.write(response.content)

		print("File retrieved successfully.")
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")

	# Define file details
	capture_file_name = file_path  # Replace with the actual file name
	captured_file_id = captured_file_id  # Replace with the actual captured file ID
	capture_file_type = "image/jpeg"  # Replace with the actual file type (e.g., "application/pdf")
	file_extension = "jpeg"  # Replace with the actual file extension (e.g., "pdf")

	# Construct the URL for the classify and extract page service
	classify_extract_url = f"{base_url}/capture/cp-rest/v2/session/services/classifyextractpage"

	# Set the headers and payload for the request
	headers = {
		'Authorization': f'Bearer {access_token}',
		'Accept': 'application/hal+json',
		'Accept-Language': 'en-US',
		'Content-Type': 'application/hal+json'
	}

	# Construct the request payload as a Python dictionary
	request_payload = {
		"serviceProps": [
			{"name": "Env", "value": "D"},
			{"name": "IncludeOcrData", "value": False},
			{"name": "Project", "value": "InformationExtraction"}
		],
		"requestItems": [
			{
				"nodeId": 1,
				"values": None,
				"files": [
					{
						"name": capture_file_name,
						"value": captured_file_id,
						"contentType": capture_file_type,
						"fileType": file_extension
					}
				]
			}
		]
	}

	# Make the POST request to classify and extract page
	try:
		response = requests.post(classify_extract_url, headers=headers, data=json.dumps(request_payload))
		response.raise_for_status()
		response_data = response.json()
		print(response_data)
	except requests.exceptions.RequestException as e:
		print(f"Error: {e}")

	import pdfplumber
	# Specify the path to your PDF file
	pdf_file_path = "output.pdf"  # Replace with the actual path to your PDF file

	# Open the PDF file using pdfplumber
	with pdfplumber.open(pdf_file_path) as pdf:
		# Get the first page (you can change this as needed)
		first_page = pdf.pages[0]

		# Extract text from the page
		text = first_page.extract_text()

		# Search for specific keywords to extract metadata (customize this based on your PDF structure)
		invoice_id = None
		# Add more variables for other metadata you want to extract

		# Example: Extracting invoice ID
		st.write(text)
