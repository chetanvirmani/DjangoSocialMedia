from django.shortcuts import render, redirect
from .forms import PostForm,ProfileForm, RelationshipForm
from .models import Post, Comment, Like, Profile, Relationship
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.http import Http404


# Create your views here.

# When a URL request matches the pattern we just defined, 
# Django looks for a function called index() in the views.py file. 

def index(request):
    """The home page for Learning Log."""
    return render(request, 'FeedApp/index.html')



@login_required #This is a decorator. It does verification, if it's true, then it allows access to the stuff under this
#This will make sure that only people that can access def profile are people who have logged in
def profile(request):
    profile = Profile.objects.filter(user=request.user) #Filter to single out the user at hand. Filter checks if the profile exists or not, if it does, then it pulls it.
    if not profile.exists(): #if the above line didn't bring back any data then:
        Profile.objects.create(user=request.user) #Then create one
    profile = Profile.objects.get(user=request.user) #we use get because now profile does exist

#Question: What does request.user do?

    if request.method != 'POST':
        form = ProfileForm(instance = profile) #ProfileForm was created in forms.py
    else:
        form = ProfileForm(instance = profile, data = request.POST)
        if form.is_valid():
            form.save()
            return redirect('FeedApp:profile')
    
    context = {'form':form}
    return render(request, 'FeedApp/profile.html', context)#Question: What does this do?

@login_required
def myfeed(request):
    comment_count_list = []
    like_count_list = [] #We're creating empty lists to contain the likes and comments
    posts = Post.objects.filter(username = request.user).order_by('-date_posted') #Post is from the models.py, in that we are filtering out the posts for the user at hand.
    #To do that, we assign the username (under the Post class in the models.py) as request.user
    #and date_posted is also an attribute of the Post Class
    for p in posts:
        c_count = Comment.objects.filter(post=p).count() 
        l_count = Like.objects.filter(post=p).count()
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts,comment_count_list,like_count_list)

    context = {'posts':posts, 'zipped_list': zipped_list}
    return render (request, 'FeedApp/myfeed.html', context)

@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
    else:
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new_post = form.save(commit=False) #Commit False means that we are saving it to database but not writing it to the database
            new_post.username = request.user
            new_post.save()
            return redirect('FeedApp:myfeed')
    

    context = {'form': form}
    return render(request, 'FeedApp/new_post.html', context)

@login_required
def comments(request,post_id):
    if request.method == 'POST' and request.POST.get("btn1"): #We are checking to see if request method is post, and if the submit button was clicked We'll do further stuff if thats request.POSTxxxx (button click) true
        comment = request.POST.get("comment")
        Comment.objects.create(post_id=post_id, username=request.user, text=comment,date_added= date.today())

    comments = Comment.objects.filter(post_id=post_id)
    post = Post.objects.get(id=post_id)

    context = {'post':post,'comments':comments}

    return render(request, 'FeedApp/comments.html', context)

