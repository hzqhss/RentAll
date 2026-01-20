from django.db import models
from django.contrib.auth.models import AbstractUser

from PIL import Image
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import post_save
from django.utils.text import slugify
import shortuuid

GENDER = (
    ("male" , "Male"),
    ("female" , "Female")
)

AVAILABILITY = (
    ("available", "Available"),
    ("unavailable", "Unavailable")
)

#more organized way to keep images so tk overload
def user_directory_path(instance, filename):
    ext = filename.split(".")[-1] #get the extension of the file
    filename = "%s.%s" % (instance.user.id, ext) #instead of long img name -> id.jpg (cth: 200_jpg)
    return 'user_{0}/{1}'.format(instance.user.id, filename) #0 = user id, 1 = filename

from django.core.exceptions import ValidationError

def validate_iium_email(value):
    if not value.lower().endswith('@live.iium.edu.my'):
        raise ValidationError('Only @live.iium.edu.my email addresses are allowed.')

class User(AbstractUser):
    full_name = models.CharField(max_length=200) #charfield tak leh ambik byk words
    username = models.CharField(max_length=50)
    email = models.EmailField(unique=True, validators=[validate_iium_email])
    phone = models.CharField(max_length=200)
    gender = models.CharField(max_length=100, choices=GENDER, default="male")
    
    otp = models.CharField(max_length=10, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self): #string representation -> if xbuat, instead of seeing each username, akan nampak object1, object2,...
        return self.username
    
class Profile(models.Model):
    pid = ShortUUIDField(length=7, max_length=25, alphabet='abcdefghijklmnopqrstuvwxyz')
    user = models.OneToOneField(User,on_delete=models.CASCADE) #1 user = 1 profile only, cascade - delete profile auto delete evrything in user 
    cover_image = models.ImageField(upload_to=user_directory_path, blank=True, null=True, default="cover.jpg")
    image = models.ImageField(upload_to=user_directory_path, blank=True, null=True, default="default.jpg")
    full_name = models.CharField(max_length=200, null=True, blank=True) #charfield tak leh ambik byk words
    phone = models.CharField(max_length=200, null=True, blank=True)
    gender = models.CharField(max_length=100, choices=GENDER, default="male")
    # relationship = models.CharField(max_length=100, choices=RELATIONSHIP, default="single")
    bio = models.CharField(max_length=200, null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)

    # country = models.CharField(max_length=200, null=True, blank=True)
    # state = models.CharField(max_length=200, null=True, blank=True)
    # city = models.CharField(max_length=200, null=True, blank=True)
    # address = models.CharField(max_length=200, null=True, blank=True)
    # working_at = models.CharField(max_length=200, null=True, blank=True)

    whatsapp = models.CharField(max_length=200, null=True, blank=True)
    instagram = models.CharField(max_length=200, null=True, blank=True)

    verified = models.BooleanField(default=False)
    # user.profile.verified = True

    followers = models.ManyToManyField(User, blank=True, related_name="followers")
    following = models.ManyToManyField(User, blank=True, related_name="following")
    friends = models.ManyToManyField(User, blank=True, related_name="friends")
    blocked = models.ManyToManyField(User, blank=True, related_name="blocked")

    date = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True, null=True) #must be true so 2 profiles xboleh ada same slug

    def __str__(self): #string representation -> if xbuat, instead of seeing each username, akan nampak object1, object2,...
            return self.user.username
    
    # overwrite the save method
    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug == None:
            uuid_key = shortuuid.uuid() #akan jd too panjang 
            uniqueid = uuid_key[:2]  # cut it to only the first 2
            self.slug = slugify(self.full_name) + "-" + str(uniqueid.lower()) #cth: kwon hoshi -> kwon-hoshi-ks
        super(Profile, self).save(*args, **kwargs) 

    #django signals code that automatically create a profile when a user is created
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    #save the profile     
    def save_user_profile(sender, instance, **Kwargs):
        instance.profile.save()   

    #connect the above two
    post_save.connect(create_user_profile, sender=User)
    post_save.connect(save_user_profile, sender=User)



