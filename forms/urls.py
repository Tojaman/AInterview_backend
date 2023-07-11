from django.urls import path, include
from . import views

urlpatterns = [
    path('',  views.FormsView.as_view(), name='form_list'),
    path('<int:user_id>/<int:pk>', views.FormView.as_view(), name='form_detail')
]