from django.db import models
import uuid
import os
from django.utils.deconstruct import deconstructible

@deconstructible
class PathRename(object):

    def __init__(self, sub_path, name):
        self.path = sub_path
        self.name = name

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(self.name, ext)
        # return the whole path to the file
        return os.path.join(self.path, filename)


class License(models.Model):
	id = models.AutoField(primary_key=True)
	# unique_id = uuid.uuid4().hex
	pco_license_image = models.ImageField(upload_to=PathRename('images', 'pco_image'))
	driver_license_image = models.ImageField(upload_to=PathRename('images', 'driver_image'))

	def __str__(self):
		return f'{self.id}'

	def get_uuid(self):
		return f'{self.id}'




class DrivingLicense(models.Model):
	unique_id = models.CharField(max_length=30)
	driver_original_image = models.CharField(max_length=50000)
	driver_face = models.CharField(max_length=50000)
	Fullname = models.CharField(max_length=255)
	DOB = models.CharField(max_length=15)
	POB = models.CharField(max_length=255)
	Issued_Date = models.CharField(max_length=15)
	Renew_Due_Date = models.CharField(max_length=15)
	Issuing_authority = models.CharField(max_length=50)
	License_Number = models.CharField(max_length=25)
	Address = models.CharField(max_length=255)
	Entitlement_categories = models.CharField(max_length=255)


	def __str__(self):
		return self.unique_id


class PCOLicense(models.Model):
	unique_id = models.CharField(max_length=30)
	pco_original_image = models.CharField(max_length=50000)
	pco_face = models.CharField(max_length=50000)
	Fullname = models.CharField(max_length=255)
	License_Number = models.CharField(max_length=25)
	Expiry_date = models.CharField(max_length=25)

	def __str__(self):
		return self.unique_id









	# def get_absolute_url(self):
 #        return reverse("newagecut:product", kwargs={
 #            'slug': self.id
 #        })



# def path_and_rename(path, name):
#     def wrapper(instance, filename):
#         ext = filename.split('.')[-1]
#         if instance.pk:
#             filename = '{}.{}'.format(instance.pk, ext)
#         else:
#             filename = '{}.{}'.format(name, ext)
#         return os.path.join(path, filename)
#     return wrapper


# def call_rename_function():
# 	unique_id = uuid.uuid4().hex
# 	path_and_rename1 = PathRename(f'{unique_id}', 'pco_image')
# 	path_and_rename2 = PathRename(f'{unique_id}', 'driver_image')
# 	return unique_id, path_and_rename1, path_and_rename2






# class PCO_License(models.Model):
# 	unique_id = unique_id
# 	license_image = models.ImageField(upload_to=f'{unique_id}')

# 	def __str__(self):
# 		return f'{unique_id}'