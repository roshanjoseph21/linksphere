from typing import Any
from django.db import models
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from django.views.generic import FormView,CreateView,TemplateView,View,UpdateView,DetailView,ListView
from social.forms import RegistrationForm,LoginForm,UserProfileForm,PostForm,CommentForm,StoryForm
from django.contrib.auth import authenticate,login,logout
from social.models import UserProfile,Posts,Comments,Stories
from social.decorators import login_required
from django.utils import timezone
from django.contrib import messages
# Create your views here.

decs=[login_required,never_cache]


class SignUpView(CreateView):
    template_name="register.html"
    form_class=RegistrationForm

    def get_success_url(self) -> str:
        return reverse("signin")

class SignInView(FormView):
    template_name="login.html"
    form_class=LoginForm

    def post(self,request,*args,**kwargs):
        form=LoginForm(request.POST)
        if form.is_valid():
            uname=form.cleaned_data.get("username")
            pwd=form.cleaned_data.get("password")
            user_object=authenticate(request,username=uname,password=pwd)
            if user_object:
                login(request,user_object)
                print("logged in successfully..........")
                return redirect("index")
            
        print("error in login")
        messages.error(request,"failed to login, invalid credentials")
        return render(request,"login.html",{"form":form}) 

@method_decorator(login_required,name="dispatch")
class IndexView(CreateView,ListView):
    template_name="index.html"
     #create and list post view in the index page
    form_class=PostForm
    model=Posts
    context_object_name="data"

    def form_valid(self, form) :
        #form.instance ponits to postform user
        form.instance.user=self.request.user
        return super().form_valid(form)
  
    #after create sucessfully, the url needs to redirect to another view.so below fun implimented
    def get_success_url(self) -> str:
        return reverse("index")
    
    #to sort post in decending order()
    def get_queryset(self):

        blocked_profile=self.request.user.profile.block.all()
        blockedprofile_id=[pr.user.id for pr in blocked_profile]
        print(blockedprofile_id)

        qs=Posts.objects.exclude(user__id__in=blockedprofile_id).order_by("-created_date")
        return qs
    
    #this method is used to override to pass additional data to html side
    def get_context_data(self, **kwargs): 
        context=super().get_context_data(**kwargs)
        current_date=timezone.now()
        context["stories"]=Stories.objects.filter(expiry_date__gte=current_date)  #list stories
        return context

@method_decorator(decs,name="dispatch")  
class SignOutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect("signin")
    
@method_decorator(decs,name="dispatch")   
class ProfileUpdateView(UpdateView):
    template_name="profile_add.html"
    form_class=UserProfileForm
    model=UserProfile

    def get_success_url(self):
        return reverse("index")
    
@method_decorator(decs,name="dispatch")     
class ProfileDetailView(DetailView):
    template_name="profile_detail.html"
    model=UserProfile
    context_object_name="data"

@method_decorator(decs,name="dispatch")  
class ProfileListView(View):
    def get(self,request,*args,**kwargs):
        qs=UserProfile.objects.all().exclude(user=request.user) #exclude will remove the loggedin user
        return render(request,"profile_list.html",{"data":qs})
    

#follow url 
@method_decorator(decs,name="dispatch")  
class FollowView(View):
    def post(self,request,*args,**kwargs):
        #print(request.POST)
        id=kwargs.get("pk")
        profile_object=UserProfile.objects.get(id=id)
        action=request.POST.get("action")
        if action == "follow":
            request.user.profile.following.add(profile_object) #add following userprofile to req .user
        elif action=="unfollow":
            request.user.profile.following.remove(profile_object)#remove following userprofile to req .user
        return redirect("index")


@method_decorator(decs,name="dispatch")  
class PostLikeView(View):
    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        post_object=Posts.objects.get(id=id)
        action=request.POST.get("action")
        print(action)
        if action == "like":
            post_object.liked_by.add(request.user)

        elif action == "dislike":
            post_object.liked_by.remove(request.user)
        
        return redirect("index")

@method_decorator(decs,name="dispatch")      
class CommentView(CreateView): #comment is gona create so create view
    template_name="index.html"
    form_class=CommentForm #which form class is gona render

    def get_success_url(self) -> str:
        return reverse("index")
    
    def form_valid(self, form) :
        #form.instance ponits to postform user
        id=self.kwargs.get("pk")
        post_object=Posts.objects.get(id=id)
        form.instance.user=self.request.user
        form.instance.post=post_object
        return super().form_valid(form)

#localhost:8000/profile/<int:pk>/block
@method_decorator(decs,name="dispatch")  
class ProfileBlockView(View):
    def post(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        #take the  profile wana block ,take pro obj
        profile_object=UserProfile.objects.get(id=id)
        action=request.POST.get("action")
        print(action)
        if action == "block":
            request.user.profile.block.add(profile_object) #request.user.profile will give the logined user
        elif action=="unblock":
            request.user.profile.block.remove(profile_object)
        
        return redirect("index")

@method_decorator(decs,name="dispatch")     
class StoriesCreateView(View):
    def post(self,request,*args,**kwargs):
        form=StoryForm(request.POST,files=request.FILES)
        if form.is_valid():
            form.instance.user=request.user
            form.save()
            return redirect("index")
        return redirect("index")
    

    


        
         

        
