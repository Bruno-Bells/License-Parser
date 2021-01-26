from django.shortcuts import render, redirect
from .forms import License_upload_Form, PCOLicenseForm, DrivingLicenseForm

import os, io
from google.cloud import vision_v1 as vision
from google.cloud.vision_v1 import types
import pandas as pd
import cv2
import numpy as np
import json
import re
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import imagehash
# from IPython.display import Image
from enum import Enum
from termcolor import colored
import boto3
from botocore.client import Config
import uuid
from io import StringIO
import base64
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import DrivingLicense, PCOLicense




# %matplotlib inline

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'Demz_vision_API_token.json'


def core_License_processor(img1, img2):

	# Path to the two License
	PCO_License = img1
	Driver_License = img2

	# client
	client = vision.ImageAnnotatorClient()
	crop_hints_params = vision.CropHintsParams(aspect_ratios=[1.77])

	# AWS Client
	with open('configfile.json') as f:
		data = json.load(f)

	ACCESS_KEY_ID = data['demz-license-user-access-key']
	ACCESS_SECRET_KEY = data['demz-license-user-secret-access-key']

	pco_BUCKET_NAME = 'pco-license'
	driver_BUCKET_NAME = 'drivers-license'
	user_BUCKET_NAME = 'license-user'


	# Drivers License response
	with io.open(img2, 'rb') as image_file1:
			content = image_file1.read()
	# content = img2
	driver_license_original_image = content
	content_image = types.Image(content=content)
	Drivers_response = client.text_detection(image=content_image)
	Drivers_response_face = client.face_detection(image=content_image)
	Drivers_texts = Drivers_response.text_annotations
	Drivers_faceAnnotations = Drivers_response_face.face_annotations

	# PCO License response
	with io.open(img1, 'rb') as image_file1:
			content = image_file1.read()
	# content = img1
	pco_license_original_image = content
	content_image = types.Image(content=content)
	PCO_response = client.text_detection(image=content_image)
	PCO_response_face = client.face_detection(image=content_image)
	PCO_texts = PCO_response.text_annotations
	PCO_faceAnnotations = PCO_response_face.face_annotations


	# Get crop hint
	def get_crop_hint(crop_hints):
		"""Detect crop hints on a single image and return the first result."""
		with io.open(crop_hints, 'rb') as image_file1:
			content = image_file1.read()
		
		# content = crop_hints
		image = vision.Image(content=content)
		
		image_context = vision.ImageContext(crop_hints_params=crop_hints_params)

		response = client.crop_hints(image=image, image_context=image_context)
		hints = response.crop_hints_annotation.crop_hints

		# Get bounds for the first crop hint using an aspect ratio of 1.77.
		vertices = hints[0].bounding_poly.vertices

		return vertices

	def crop_Driver_hint(image_file):
		"""Crop the image using the hints in the vector list."""
		vects = get_crop_hint(image_file)
	#     response_face = Drivers_response_face
		faceAnnotations = Drivers_faceAnnotations
		try:
			face_bounds = []
			for face in faceAnnotations:
				face_vertices = (['({0},{1})'.format(vertex.x, vertex.y) for vertex in face.bounding_poly.vertices])
				face_bounds.append(face_vertices)
			bound_1 = face_bounds[0][0]
			bound_2 = face_bounds[0][2]
			bound_1 = eval(bound_1)
			bound_2 = eval(bound_2)

			im = Image.open(image_file)

			im2 = im.crop([bound_1[0], bound_1[1],
						  bound_2[0] - 1, bound_2[1] - 1])
		#     plt.imshow(im2)
		#     im2.save('output-crop.jpg', 'JPEG')
			print('Saved new image to output-crop.jpg')
			return im2
		except:
			with io.open('media_root/no_face.png', 'rb') as image_file1:
				im2 = image_file1.read()
			print("No Image Detected")
			return im2
			# return "No Image Detected"


	def crop_PCO_hint(image_file):
		"""Crop the image using the hints in the vector list."""
		vects = get_crop_hint(image_file)
	#     response_face = PCO_response_face
		faceAnnotations = PCO_faceAnnotations
		try:
			face_bounds = []
			for face in faceAnnotations:
				face_vertices = (['({0},{1})'.format(vertex.x, vertex.y) for vertex in face.bounding_poly.vertices])
				face_bounds.append(face_vertices)
			bound_1 = face_bounds[0][0]
			bound_2 = face_bounds[0][2]
			bound_1 = eval(bound_1)
			bound_2 = eval(bound_2)

			im = Image.open(image_file)

			im2 = im.crop([bound_1[0], bound_1[1],
						  bound_2[0] - 1, bound_2[1] - 1])
		#     plt.imshow(im2)
		#     im2.save('output-crop.jpg', 'JPEG')
			print('Saved new image to output-crop.jpg')
			return im2
		except:
			with io.open('media_root/no_face.png', 'rb') as image_file1:
				im2 = image_file1.read()
			print("No Image Detected")
			return im2
			# return "No Image Detected"

	Driver_Image = crop_Driver_hint(img2)
	PCO_IMage = crop_PCO_hint(img1)


	def Processor(Drivers_texts, PCO_texts):
		Drivers_contents = []
		PCO_contents = []
		
		# Extract Driver License Contents
		for text in Drivers_texts:
			Drivers_contents.append(text.description)
		
		# Extract PCO License Contents
		for text in PCO_texts:
			PCO_contents.append(text.description)
			
		Driver_String_Content = Drivers_contents[0]
		PCO_String_Content = PCO_contents[0]
		
	#     print(PCO_contents)

		# Process the PCO License
		def Process_PCO_License(PCO_String_Content):
			 try:
			 	if 'Expire Date' in PCO_String_Content:
			 		new_pco_list = PCO_String_Content.split('Expire Date:')
			 	elif 'Expiry Date:' in PCO_String_Content:
			 		new_pco_list = PCO_String_Content.split('Expiry Date:')
			 	else:
			 		new_pco_list = PCO_String_Content.split('Expiry Date')
			 	new_pco = new_pco_list[-1]
			 	Expiry_date = new_pco_list[-1].split('\n')
			 	Expiry_date = [date for date in Expiry_date if date != ''][0]
			 	new_pco_content = new_pco_list[0]

			 	def get_pco_license_NO(new_pco_content):
			 		license_NO = re.findall(r'\d',new_pco_content)
			 		license_NO = ''.join(license_NO)
			 		return license_NO
			 	PCO_license_NO = get_pco_license_NO(new_pco_content)
			 	new_pco_content = new_pco_content.split(PCO_license_NO)

			 	new_pco_content = new_pco_content[-1]
			 	new_pco_content = new_pco_content.split('\n')

			 	new_pco_content = [name for name in new_pco_content if name != '']
			 	First_Name = new_pco_content[0]
			 	Other_Name = new_pco_content[-1]
			 	Full_Name = First_Name + ' '+ Other_Name
			 	Full_Name = Full_Name.split(' ')
			 	Full_Name = sorted(Full_Name)
			 	Full_Name = ' '.join(Full_Name)
			 	print(Full_Name)

			 	PCO_CONTENT = {}
			 	PCO_CONTENT['Full_Name'] = Full_Name
			 	#         PCO_CONTENT['Other Name'] = new_pco_content[-1]
			 	PCO_CONTENT['License Number'] = PCO_license_NO
			 	PCO_CONTENT['Expiry Date'] = Expiry_date
			 	return PCO_CONTENT
			 except:
			 	PCO_CONTENT = {'Contents': "The Uploaded Document does not seem like a PCO License"}
		
	#     print(Process_PCO_License(PCO_String_Content))
		def Process_Driver_License(Driver_String_Content):
	#         print(Driver_String_Content)
			
			if 'DRIVING LICENCE' in Driver_String_Content:
				if 'DRIVING LICENCE' in Driver_String_Content:
					Driver_contents = Driver_String_Content.split('DRIVING LICENCE')[-1]
				elif '1.' in Driver_String_Content:
					Driver_contents = re.split('1.', Driver_String_Content, 1)[-1]
				else:
					Driver_contents = Driver_String_Content
					print('No Split Found')
		#       Dates
				dates = re.findall(r"([1-9]|0[1-9]|1[0-9]|2[0-9]|3[0-1])(\.|-|/)([1-9]|0[1-9]|1[0-2])(\.|-|/)(19[0-9][0-9]|20[0-9][0-9]|[0-9][0-9])", Driver_contents)
				new_dates = []
				for date in dates:
					dat = ''.join(date)
					new_dates.append(dat)
				if len(new_dates) >= 3:
					date_and_POB = re.search(f'{new_dates[0]}.*\n', Driver_contents).group(0).split('\n')[0]
					DOB = new_dates[0]
					POB = date_and_POB.split(DOB)[-1]
					issued_date = new_dates[1]
					Renew_due_date = new_dates[2]
				else:
					dates = re.findall("\d\d.*\d\d",Driver_contents)
					date_and_POB = re.search(f'{dates[0]}.*\n', Driver_contents).group(0).split('\n')[0]
					DOB = dates[0]
					POB = date_and_POB.split(DOB)[-1]
					issued_date = dates[1]
					Renew_due_date = dates[2]

		#       Names
				Names = Driver_contents.split(date_and_POB)[0]
				Names = re.split('\d.',Names)
				Names = ' '.join(Names)
				Names = Names.split('\n')
				Names = [name.strip() for name in Names if name]
				Names = [name for name in Names if name]
				if Names[0] == 'UK':
					Names = Names[1:]
				if len(Names) > 2:
					First_Name = Names[0]
					if not 'UK' in Names:
						Other_Name = ' '.join(Names[1:]) 
					else:
						Other_Name = Names[1]
					Full_Name = First_Name + ' '+ Other_Name
					Full_Name = Full_Name.split(' ')
					Full_Name = sorted(Full_Name)
					Full_Name = ' '.join(Full_Name)
					print(Full_Name)
				else:
					First_Name = Names[0]
					Other_Name = Names[1]
					Full_Name = First_Name + ' '+ Other_Name
					Full_Name = Full_Name.split(' ')
					Full_Name = sorted(Full_Name)
					Full_Name = ' '.join(Full_Name)
					print(Full_Name)
					
		#       Authority
				Authority = re.search(f'{issued_date}.*\n', Driver_contents).group(0)
				Authority_EX = re.findall("\d\d.*\d\d", Authority)
				authority_date = []
				for date in Authority_EX:
					dat = ''.join(date)
					authority_date.append(dat)
				Authority = Authority.split(authority_date[-1])[-1]
				Authority = Authority.split(' ')[-1]
				Authority = Authority.split('\n')[0]

		#       LICENSE NUMBER
				License_No = Driver_contents.split(Renew_due_date)[1]
				License_No = License_No.split('\n')
				License_No = [license.strip() for license in License_No if license]
				match_license = []
				for license in License_No:
					if re.search("\w.*\d", license):
						match_license.append(license)
				if len(match_license) > 0:
					License_No = match_license[0]
				else:
					License_No = 'None'

		#       Address
				Address = Driver_contents.split(License_No)[-1]
				Address_list = Address.split('\n')

				# Merge the Address if it continues in another line
				output = []
				for i in range(len(Address_list)-1):
					if str(Address_list[i]).endswith(','):
						new_word = Address_list[i] +' '+ Address_list[i+1]
						output.append(new_word)
						next_word = Address_list[i+1]
						Address_list.remove(next_word)
					elif Address_list[i] == max(Address_list, key=len) and str(Address_list[i]).endswith('.'):
						new_word = Address_list[i] +' '+ Address_list[i+1]
						output.append(new_word)
						next_word = Address_list[i+1]
						Address_list.remove(next_word)
					else:
						new_word = Address_list[i]
						output.append(new_word)

				Address_list = output  
				Address = max(Address_list, key=len)
				if Address.isupper():
					Address = Address
				elif max(Address_list, key=len):
					Address = Address
				else:
					Address = [address for address in Address_list if address.isupper()][0]

				# Entitlement categoory
				Entitlement_categoory = Driver_contents.split(License_No)[-1]
				Entitlement_categoory = Entitlement_categoory.split('\n')
				Entitlement_categoory = [category for category in Entitlement_categoory if category][-1]
				if Entitlement_categoory == max(Address_list, key=len):
					Entitlement_categoory = 'None'
				elif re.search(f"{Entitlement_categoory}", Address) :
					Entitlement_categoory = 'None'
				else:
					Entitlement_categoory = Entitlement_categoory.split(' ')[-1]
					Entitlement_categoory  = Entitlement_categoory


				DRIVER_CONTENT = {}

				DRIVER_CONTENT['Full_Name'] = Full_Name
	#             DRIVER_CONTENT['Other Name'] = Other_Name
				DRIVER_CONTENT['Date of birth'] = DOB
				DRIVER_CONTENT['Place of birth'] = POB
				DRIVER_CONTENT['Issued Date'] = issued_date
				DRIVER_CONTENT['Renew Due Date'] = Renew_due_date
				DRIVER_CONTENT['Issuing authority'] = Authority
				DRIVER_CONTENT['License Number'] = License_No
				DRIVER_CONTENT['Address'] = Address
				DRIVER_CONTENT['Entitlement categories'] = Entitlement_categoory

				return DRIVER_CONTENT
			else:
				print('Document is Not a Driving License')
				DRIVER_CONTENT = {'Contents': "The Uploaded Document does not seem like a Driving License"}
				return DRIVER_CONTENT
		
		PCO_CONTENT = Process_PCO_License(PCO_String_Content)
		DRIVER_CONTENT = Process_Driver_License(Driver_String_Content)
			
		return PCO_CONTENT, DRIVER_CONTENT 

	PCO_CONTENT, DRIVER_CONTENT = Processor(Drivers_texts, PCO_texts)

	# PCO_CONTENT
	for x, y in PCO_CONTENT.items():
		print(x +":  " + colored(y, 'green'))
	#     print(f"{x}\x1b[31m{':  ' + y}\x1b[0m")

	# DRIVER_CONTENT
	for x, y in DRIVER_CONTENT.items():
		print(x +":  " + colored(y, 'blue'))
	#     print(f"{x}\x1b[31m{':  ' + y}\x1b[0m")


	def Compare_License(Driver_Content, PCO_Content, Driver_Image, PCO_IMage):
	
		def check_Match_Names(Driver_Content, PCO_Content):
			Driver_Full_Name = Driver_Content['Full_Name'].upper()       
			PCO_Full_Name = PCO_Content["Full_Name"].upper()
			
			Names_Match = {}
			if Driver_Full_Name == PCO_Full_Name:
				Names_Match["Full_Name_Matched"] = True
			else:
				Names_Match["Full_Name_Matched"] = False
				
			
			
			return Names_Match
		def check_Image_Similarities(Driver_Image, PCO_IMage):
			
			hash0 = imagehash.average_hash(Driver_Image)
			hash1 = imagehash.average_hash(PCO_IMage) 
			cutoff = 5

			Image_Similar = {}
			if hash0 - hash1 < cutoff:
				Image_Similar["images_similar"] = True
				print('images_are_similar')
				print('')
			else:
				Image_Similar["images_similar"] = False
				print('images are not similar')
				print('')
			return Image_Similar
		try:
			compared_names = check_Match_Names(Driver_Content, PCO_Content)
		except:
			compared_names = {"Full_Name_Matched": None}
		try:
			compared_images = check_Image_Similarities(Driver_Image, PCO_IMage)
		except:
			compared_images = {"images_similar": None}
		result = {**compared_names, **compared_images}

		return result
	
	result = Compare_License(DRIVER_CONTENT, PCO_CONTENT, Driver_Image, PCO_IMage)

	# Display Results
	for x,y in result.items():
		if y == True:
			print(x +":  " + colored(y, 'green'))
		else:
			print(x +":  " + colored(y, 'green'))

	unique_id = uuid.uuid4().hex
	print(unique_id)

	# data

	pco_original_image = open(img1, 'rb')
	driver_original_image = open(img2, 'rb')

	pco_cropped_image = PCO_IMage
	driver_cropped_image = Driver_Image

	try:
		buf = io.BytesIO()
		pco_cropped_image.save(buf, format='PNG')
		pco_cropped_image = buf.getvalue()
	except:
		pco_cropped_image = pco_cropped_image

	try:
		buf = io.BytesIO()
		driver_cropped_image.save(buf, format='PNG')
		driver_cropped_image = buf.getvalue()
	except:
		driver_cropped_image = driver_cropped_image


	pco_details = json.dumps(PCO_CONTENT)
	driver_details = json.dumps(DRIVER_CONTENT)
	pco_and_driver_license = {'PCO_LICENSE':unique_id, 'DRIVER_LICENSE':unique_id}
	pco_and_driver_license = json.dumps(pco_and_driver_license)
	new_pco_details = PCO_CONTENT
	new_driver_details = DRIVER_CONTENT

	if result['Full_Name_Matched'] == True:
		username = DRIVER_CONTENT['Full_Name'].split(' ')
		username = '-'.join(username)
	else:
		username = None


	# Upload to PCO-license bucket
	s3 = boto3.resource(
		's3',
		aws_access_key_id=ACCESS_KEY_ID,
		aws_secret_access_key=ACCESS_SECRET_KEY,
		config=Config(signature_version='s3v4')
	)

	s3.Bucket(pco_BUCKET_NAME).put_object(Key=f'{unique_id}/user_image.png', Body=pco_cropped_image, Tagging=f'unique_id={unique_id}')
	s3.Bucket(pco_BUCKET_NAME).put_object(Key=f'{unique_id}/user_detail.json', Body=pco_details, Tagging=f'unique_id={unique_id}')

	print ("Done")


	# Upload to Driver-license bucket
	s3 = boto3.resource(
		's3',
		aws_access_key_id=ACCESS_KEY_ID,
		aws_secret_access_key=ACCESS_SECRET_KEY,
		config=Config(signature_version='s3v4')
	)

	s3.Bucket(driver_BUCKET_NAME).put_object(Key=f'{unique_id}/user_image.png', Body=driver_cropped_image, Tagging=f'unique_id={unique_id}')
	s3.Bucket(driver_BUCKET_NAME).put_object(Key=f'{unique_id}/user_detail.json', Body=driver_details, Tagging=f'unique_id={unique_id}')

	print ("Done")


	# Upload to user-license bucket
	s3 = boto3.resource(
		's3',
		aws_access_key_id=ACCESS_KEY_ID,
		aws_secret_access_key=ACCESS_SECRET_KEY,
		config=Config(signature_version='s3v4')
	)

	s3.Bucket(user_BUCKET_NAME).put_object(Key=f'{unique_id}/pco_user_image.png', Body=pco_original_image, Tagging=f'unique_id={unique_id}')
	s3.Bucket(user_BUCKET_NAME).put_object(Key=f'{unique_id}/driver_user_image.png', Body=driver_original_image, Tagging=f'unique_id={unique_id}')
	s3.Bucket(user_BUCKET_NAME).put_object(Key=f'{unique_id}/user_info.json', Body=pco_and_driver_license, Tagging=f'unique_id={unique_id}')

	print ("Done")

	pco_original_image.close()
	driver_original_image.close()

	return pco_license_original_image, driver_license_original_image, pco_cropped_image, driver_cropped_image, new_pco_details, new_driver_details, result, unique_id

		

def home(request):
	if request.method == 'POST' and request.FILES['filename1']:
		pco_license_image = request.FILES['filename1']
		driver_license_image = request.FILES['filename2']
		fs = FileSystemStorage()
		PCO_IMAGE = fs.save(pco_license_image.name, pco_license_image)
		DRIVER_IMAGE = fs.save(driver_license_image.name, driver_license_image)
		PCO_IMAGE = fs.path(PCO_IMAGE)
		print(PCO_IMAGE)
		DRIVER_IMAGE = fs.path(DRIVER_IMAGE)
		pco_original_image, driver_original_image, pco_cropped_image, driver_cropped_image, pco_details, driver_details, result, unique_id = core_License_processor(PCO_IMAGE, DRIVER_IMAGE)
		# Delete Image
		os.remove(PCO_IMAGE)
		os.remove(DRIVER_IMAGE)
		# print(pco_original_image)
		# buffer = StringIO()
		# pco_original_image.savefig(buffer, "PNG")
		# pco_original_image = base64.b64encode(buffer.getvalue())
		# print(pco_original_image.__dir__())
		pco_original_image = base64.b64encode(pco_original_image).decode('utf-8')
		driver_original_image = base64.b64encode(driver_original_image).decode('utf-8')
		pco_cropped_image = base64.b64encode(pco_cropped_image).decode('utf-8')
		driver_cropped_image = base64.b64encode(driver_cropped_image).decode('utf-8')

		# DRIVER_LICENSE
		drivingLicense = DrivingLicense()
		drivingLicense.unique_id = unique_id
		drivingLicense.Fullname = driver_details["Full_Name"]
		drivingLicense.DOB = driver_details["Date of birth"]
		drivingLicense.POB = driver_details["Place of birth"]
		drivingLicense.Issued_Date = driver_details["Issued Date"]
		drivingLicense.Renew_Due_Date = driver_details["Renew Due Date"]
		drivingLicense.Issuing_authority = driver_details["Issuing authority"]
		drivingLicense.License_Number = driver_details["License Number"]
		drivingLicense.Address = driver_details["Address"]
		drivingLicense.Entitlement_categories = driver_details["Entitlement categories"]
		drivingLicense.driver_original_image = driver_original_image
		drivingLicense.driver_face = driver_cropped_image
		drivingLicense.save()


		# PCO License
		pcoLicense = PCOLicense()
		pcoLicense.unique_id = unique_id
		pcoLicense.pco_original_image = pco_original_image
		pcoLicense.pco_face = pco_cropped_image
		pcoLicense.Fullname = pco_details["Full_Name"]
		pcoLicense.License_Number = pco_details["License Number"]
		pcoLicense.Expiry_date = pco_details["Expiry Date"]
		pcoLicense.save()


		# get the contents
		driverContents = DrivingLicense.objects.filter(unique_id=unique_id)
		pcoContents = PCOLicense.objects.filter(unique_id=unique_id)


		# contents = contents.split('\n')[0]

		return render(request, 'processed.html', {
			'driverContents': driverContents,
			'pcoContents': pcoContents ,
			'unique_id':unique_id,
			'result' : result
		})
	return render(request, 'index.html')
	# 	return render(request, 'processed.html', {
	# 		'pco_original_image' : pco_original_image, 
	# 		'driver_original_image' : driver_original_image, 
	# 		'pco_cropped_image' : pco_cropped_image, 
	# 		'driver_cropped_image' : driver_cropped_image, 
	# 		'pco_details' : pco_details,
	# 		'driver_details' : driver_details,
	# 		# 'pco_and_driver_license' : pco_and_driver_license, 
	# 		'result' : result
	# 	})
	# return render(request, 'index.html')

def extracted_info(request):
	return render(request, 'processed.html')

def edited_info(request, unique_id):

	PCO_contents = PCOLicense.objects.filter(unique_id=unique_id)
	Driver_contents = DrivingLicense.objects.filter(unique_id=unique_id)
	# print('PCO_contents', PCO_contents.Fullname)

	unique_id = unique_id

	context = {

		'pcoContents': PCO_contents,
		'driverContents': Driver_contents,
		'unique_id':unique_id
	}

	return render(request, 'processed.html', context)


def Edit_Driving_license(request, unique_id):
	drivingLicense_update = DrivingLicense.objects.get(unique_id=unique_id)
	print(drivingLicense_update.Fullname)
	print(drivingLicense_update.DOB)
	if request.method == 'POST':
		# print('KKKKKKKKKKKKKKKKKk')
		instance = {'Full_Name': drivingLicense_update.Fullname, 'Date of birth':drivingLicense_update.DOB, 'Place of birth':drivingLicense_update.POB, 'Issued Date':drivingLicense_update.Issued_Date, 'Renew Due Date': drivingLicense_update.Renew_Due_Date, 'Issuing authority':drivingLicense_update.Issuing_authority, 'License Number':drivingLicense_update.License_Number, 'Address':drivingLicense_update.Address, 'Entitlement categories':drivingLicense_update.Entitlement_categories}
		
		form = DrivingLicenseForm(request.POST or None, initial={'Fullname': drivingLicense_update.Fullname, 'DOB':drivingLicense_update.DOB, 'POB':drivingLicense_update.POB, 'Issued_Date':drivingLicense_update.Issued_Date, 'Renew_Due_Date': drivingLicense_update.Renew_Due_Date, 'Issuing_authority':drivingLicense_update.Issuing_authority, 'License_Number':drivingLicense_update.License_Number, 'Address':drivingLicense_update.Address, 'Entitlement_categories':drivingLicense_update.Entitlement_categories})
		if form.is_valid():
			drivingLicense_update.Fullname = form.cleaned_data["Fullname"]
			drivingLicense_update.DOB = form.cleaned_data["DOB"]
			drivingLicense_update.POB = form.cleaned_data["POB"]
			drivingLicense_update.Issued_Date = form.cleaned_data["Issued_Date"]
			drivingLicense_update.Renew_Due_Date = form.cleaned_data["Renew_Due_Date"]
			drivingLicense_update.Issuing_authority = form.cleaned_data["Issuing_authority"]
			drivingLicense_update.License_Number = form.cleaned_data["License_Number"]
			drivingLicense_update.Address = form.cleaned_data["Address"]
			drivingLicense_update.Entitlement_categories = form.cleaned_data["Entitlement_categories"]
			drivingLicense_update.save()
			form.save()

			# drivingLicense_update = DrivingLicense.objects.get(unique_id=unique_id)
			instance = {'Full_Name': drivingLicense_update.Fullname, 'Date of birth':drivingLicense_update.DOB, 'Place of birth':drivingLicense_update.POB, 'Issued Date':drivingLicense_update.Issued_Date, 'Renew Due Date': drivingLicense_update.Renew_Due_Date, 'Issuing authority':drivingLicense_update.Issuing_authority, 'License Number':drivingLicense_update.License_Number, 'Address':drivingLicense_update.Address, 'Entitlement categories':drivingLicense_update.Entitlement_categories}
			driver_details = json.dumps(instance)

			# Update and Upload to AWS
			# AWS Client
			with open('configfile.json') as f:
				data = json.load(f)

			ACCESS_KEY_ID = data['demz-license-user-access-key']
			ACCESS_SECRET_KEY = data['demz-license-user-secret-access-key']

			pco_BUCKET_NAME = 'pco-license'
			driver_BUCKET_NAME = 'drivers-license'
			user_BUCKET_NAME = 'license-user'

			# Upload to Driver-license bucket
			s3 = boto3.resource(
				's3',
				aws_access_key_id=ACCESS_KEY_ID,
				aws_secret_access_key=ACCESS_SECRET_KEY,
				config=Config(signature_version='s3v4')
			)

			s3.Bucket(driver_BUCKET_NAME).put_object(Key=f'{unique_id}/user_detail.json', Body=driver_details, Tagging=f'unique_id={unique_id}')

			print ("Done")

			return redirect('edited_info', unique_id)

	else:
		form = DrivingLicenseForm(request.POST or None, initial={'Fullname': drivingLicense_update.Fullname, 'DOB':drivingLicense_update.DOB, 'POB':drivingLicense_update.POB, 'Issued_Date':drivingLicense_update.Issued_Date, 'Renew_Due_Date': drivingLicense_update.Renew_Due_Date, 'Issuing_authority':drivingLicense_update.Issuing_authority, 'License_Number':drivingLicense_update.License_Number, 'Address':drivingLicense_update.Address, 'Entitlement_categories':drivingLicense_update.Entitlement_categories})
	return render(request, 'edit_driving_license.html', {'form': form})


def Edit_PCO_license(request, unique_id):
	pcoLicense_update = PCOLicense.objects.get(unique_id=unique_id)
	# if request.method == 'POST':
	instance = {'Fullname': pcoLicense_update.Fullname, 'License_Number': pcoLicense_update.License_Number, 'Expiry_date':pcoLicense_update.Expiry_date}
	form = PCOLicenseForm(request.POST or None, initial=instance)
	if form.is_valid():
		pcoLicense_update.Fullname = form.cleaned_data["Fullname"]
		pcoLicense_update.License_Number = form.cleaned_data["License_Number"]
		pcoLicense_update.Expiry_date = form.cleaned_data["Expiry_date"]
		pcoLicense_update.save()
		form.save()

		pcoLicense_update = PCOLicense.objects.get(unique_id=unique_id)

		# UPloading to AWS
		pcoDetails = {'Full_Name': pcoLicense_update.Fullname, 'License Number': pcoLicense_update.License_Number, 'Expiry Date':pcoLicense_update.Expiry_date}
		pco_details = json.dumps(pcoDetails)

		with open('configfile.json') as f:
			data = json.load(f)

		ACCESS_KEY_ID = data['demz-license-user-access-key']
		ACCESS_SECRET_KEY = data['demz-license-user-secret-access-key']

		pco_BUCKET_NAME = 'pco-license'
		driver_BUCKET_NAME = 'drivers-license'
		user_BUCKET_NAME = 'license-user'

		# Upload to PCO-license bucket
		s3 = boto3.resource(
			's3',
			aws_access_key_id=ACCESS_KEY_ID,
			aws_secret_access_key=ACCESS_SECRET_KEY,
			config=Config(signature_version='s3v4')
		)

		s3.Bucket(pco_BUCKET_NAME).put_object(Key=f'{unique_id}/user_detail.json', Body=pco_details, Tagging=f'unique_id={unique_id}')

		print ("Done")

		return redirect('edited_info', unique_id)
	return render(request, 'edit_pco_license.html', {'form': form})








