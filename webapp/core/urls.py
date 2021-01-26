from django.urls import path
from . import views


urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('extracted_info', views.extracted_info, name='extracted_info'),
    path('edited_info/<str:unique_id>/', views.edited_info, name='edited_info'),
    path('Edit_Driving_license/<str:unique_id>/', views.Edit_Driving_license, name='Edit_Driving_license'),
    path('Edit_PCO_license/<str:unique_id>//', views.Edit_PCO_license, name='Edit_PCO_license')

]