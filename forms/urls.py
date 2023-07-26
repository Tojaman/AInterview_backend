from django.urls import path, include
from forms import views

urlpatterns = [
    path('', views.FormsAllView.as_view(), name='form_list'),
    path('user/<int:pk>', views.FormsUserView.as_view(), name='form_detail'),
    path('qnum/', views.QesNumPostView.as_view(), name='qes_num'),
    path('qnum/<int:qesnum_id>', views.QesNumView.as_view(), name='qes_num'),
]