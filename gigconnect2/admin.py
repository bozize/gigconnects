from django.contrib import admin
from .models import User, FreelancerProfile, ClientProfile, JobCategory, Skill, Job, JobApplication

# Register the User model with the admin
admin.site.register(User)

# Optionally, register the profiles if you want to manage them in the admin as well
admin.site.register(FreelancerProfile)
admin.site.register(ClientProfile)

admin.site.register(JobCategory)
admin.site.register(Skill)
admin.site.register(Job)
admin.site.register(JobApplication)