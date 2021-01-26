from django.contrib import admin
from .models import License, DrivingLicense, PCOLicense

admin.site.register(License)
admin.site.register(DrivingLicense)
admin.site.register(PCOLicense)
# admin.site.register(PCO_License)