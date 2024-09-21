from rest_framework import serializers
from django.contrib.auth.models import User
from .models import JobCategory, Skill, ClientProfile, FreelancerProfile, Job, JobApplication
from .models import User
from .models import FreelancerProfile
from .models import ClientProfile



# Serializer for User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'id']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        role = validated_data.pop('role', User.Role.ADMIN)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.role = role
        user.save()
        return user

# Serializer for User Login
class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

# Serializer for JobCategory
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']

class JobCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'skills']

# Serializer for FreelancerProfile
class FreelancerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = serializers.PrimaryKeyRelatedField(many=True, queryset=Skill.objects.all())
    job_categories = serializers.PrimaryKeyRelatedField(many=True, queryset=JobCategory.objects.all())

    class Meta:
        model = FreelancerProfile
        fields = ['id', 'user', 'bio', 'skills', 'job_categories']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['skills'] = [skill.id for skill in instance.skills.all()]
        representation['job_categories'] = [category.id for category in instance.job_categories.all()]
        return representation

class FreelancerProfileDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    job_categories = JobCategorySerializer(many=True, read_only=True)

    class Meta:
        model = FreelancerProfile
        fields = ['id', 'user', 'bio', 'skills', 'job_categories']


class JobSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=JobCategory.objects.all())
    required_skills = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True)
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)  # Client is usually the authenticated user

    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'pay', 'category', 'required_skills', 'client', 'created_at', 'updated_at']

    def create(self, validated_data):
        # Automatically assign the authenticated user as the client
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        # For displaying related fields as strings in the response
        representation = super().to_representation(instance)
        representation['category'] = str(instance.category)
        representation['required_skills'] = [str(skill) for skill in instance.required_skills.all()]
        representation['client'] = str(instance.client)
        return representation

class JobApplicationSerializer(serializers.ModelSerializer):
    estimated_completion_time_display = serializers.CharField(source='get_estimated_completion_time_display', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'user', 'job_title', 'user_username', 'cover_letter', 'proposed_pay', 'estimated_completion_time', 
                  'estimated_completion_time_unit', 'estimated_completion_time_display', 'status', 'created_at', 'updated_at']
    def validate_title(self, value):
        if not value or value.isdigit():
            raise serializers.ValidationError("Please provide a descriptive title for your application.")
        return value



class ClientProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ClientProfile
        fields = ['id', 'user', 'company_name', 'website']
        read_only_fields = ['id', 'user']

    def update(self, instance, validated_data):
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.website = validated_data.get('website', instance.website)
        instance.save()
        return instance