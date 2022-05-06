from django.urls import path
from . import views

app_name = 'FeedApp'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/', views.profile, name = 'profile'),
    path('myfeed',views.myfeed, name = 'myfeed'), #This creates a link right next to the home
    path('new_post/',views.new_post, name='new_post'),
    path('comments/<int:post_id>/', views.comments, name='comments'), #We are adding <int:postId> here because we need to see the comment for a particular post number
    ]

