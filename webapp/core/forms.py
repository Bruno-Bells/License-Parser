from django import forms
from .models import License, DrivingLicense, PCOLicense


class License_upload_Form(forms.ModelForm):
	class Meta:
		model = License
		fields = ['pco_license_image', 'driver_license_image']



class DrivingLicenseForm(forms.ModelForm):
	class Meta:
		model = DrivingLicense
		fields = ['Fullname', 'DOB', 'POB', 'Issued_Date', 'Renew_Due_Date', 'Issuing_authority', 'License_Number', 'Address', 'Entitlement_categories']



class PCOLicenseForm(forms.ModelForm):
	class Meta:
		model = PCOLicense
		fields = ['Fullname', 'License_Number', 'Expiry_date']
# class PCO_License_upload_Form(forms.ModelForm):
# 	class Meta:
# 		model = PCO_License
# 		fields = ['license_image']





