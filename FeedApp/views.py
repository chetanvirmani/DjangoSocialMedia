from shutil import unregister_archive_format
from django.dispatch import receiver
from django.shortcuts import render, redirect

from FeedApp import admin
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
            return redirect('FeedApp:friends')
    
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
def friendsfeed(request):
    comment_count_list = []
    like_count_list = [] #We're creating empty lists to contain the likes and comments
    
    friends = Profile.objects.filter(user=request.user).values('friends')
    posts = Post.objects.filter(username__in = friends).order_by('-date_posted') #Post is from the models.py, in that we are filtering out the posts for the user at hand.
    #To do that, we assign the username (under the Post class in the models.py) as request.user
    #and date_posted is also an attribute of the Post Class
    for p in posts:
        c_count = Comment.objects.filter(post=p).count() 
        l_count = Like.objects.filter(post=p).count()
        comment_count_list.append(c_count)
        like_count_list.append(l_count)
    zipped_list = zip(posts,comment_count_list,like_count_list)

    if request.method == 'POST' and request.POST.get("like"):
        post_to_like = request.POST.get("like") #Like is the name of the button set in friendsfeed html and posttolike is the post id
        like_already_exists = Like.objects.filter(post_id = post_to_like, username=request.user)
        if not like_already_exists.exists():
            Like.objects.create(post_id = post_to_like, username = request.user)
            return redirect("FeedApp:friendsfeed")


    context = {'posts':posts, 'zipped_list': zipped_list}
    return render (request, 'FeedApp/friendsfeed.html', context)

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

@login_required
def friends(request):
    admin_profile = Profile.objects.get(user = 1) #the first user who registered (me) will be the admin
    user_profile = Profile.objects.get(user = request.user)

    #to get My friends
    user_friends = user_profile.friends.all()
    user_friends_profiles = Profile.objects.filter(user__in = user_friends) #list of user's friends

    #to get Friend Requests sent
    user_relationships = Relationship.objects.filter(sender = user_profile) 
    request_sent_profiles = user_relationships.values('receiver') #collection of profiles that user has sent request to

    # to get eligble profiles to whom the request can be sent, exclude user, admin, and friend requests already sent
    all_profiles = Profile.objects.exclude(user=request.user).exclude(id__in=user_friends_profiles).exclude(id__in= request_sent_profiles)


    #to get requests recieved by the user
    request_received_profiles = Relationship.objects.filter(receiver = user_profile, status= 'sent') #list of received friend requests

    if not user_relationships.exists(): #sending the first request to admin. That is, if not relationships exist, then the profile has just been created and the following would happen
        Relationship.objects.create(sender = user_profile, receiver = admin_profile, status='sent')
    

    #check which button was pressed? sending request or accepting request?

    #process all send requests
    if request.method == 'POST' and request.POST.get("send_requests"):
        receivers = request.POST.getlist("send_requests") #get the list of all the checkboxes that were checked from the input in frieds.html
        for receiver in receivers:
            receiver_profile = Profile.objects.get(id = receiver)
            Relationship.objects.create(sender = user_profile, receiver = receiver_profile, status = 'sent')
        return redirect('FeedApp:friends')

    #process all recieve requests
    if request.method == 'POST' and request.POST.get("receive_requests"):
        senders = request.POST.getlist("receive_requests")
        for sender in senders:
            Relationship.objects.filter(id = sender).update(status='accepted')
        
    
            #create a relationship object to access the sender's user id
            # to add to the friends list of the user
            relationship_obj = Relationship.objects.get(id = sender)
            user_profile.friends.add(relationship_obj.sender.user) #we are getting the user id of the person who sent the request that we are adding that person to friends in the user profile

            #add user to friends list of the sender's profile
            relationship_obj.sender.friends.add(request.user)


    context = {'user_friends_profiles':user_friends_profiles,'user_relationships':user_relationships,'all_profiles':all_profiles, 'request_received_profiles':request_received_profiles}

    return render(request, 'FeedApp/friends.html', context)

