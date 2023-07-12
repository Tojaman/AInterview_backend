from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.FormsAllView.as_view(), name='form_list'),
    path('<int:user_id>/<int:pk>', views.FormsUserView.as_view(), name='form_detail')
]