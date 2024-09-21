from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, UserLoginSerializer, JobCategorySerializer, SkillSerializer, FreelancerProfileSerializer, JobSerializer, JobApplicationSerializer, ClientProfileSerializer, FreelancerProfileDetailSerializer
from django.contrib.auth import authenticate
from .models import User, JobCategory, Skill, Job, JobApplication
from .models import User, FreelancerProfile, ClientProfile
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

@api_view(['POST', 'GET'])
def signup_client(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = User.Role.CLIENT
            user.set_password(request.data['password'])
            user.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'GET':
        
        clients = User.objects.filter(role=User.Role.CLIENT)
        serializer = UserSerializer(clients, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def signup_freelancer(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.role = User.Role.FREELANCER
        user.set_password(request.data['password'])
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            profile_complete = False
            if user.role == User.Role.FREELANCER:
                profile, _ = FreelancerProfile.objects.get_or_create(user=user)
                profile_complete = bool(profile.bio and profile.skills.exists())
            elif user.role == User.Role.CLIENT:
                profile, _ = ClientProfile.objects.get_or_create(user=user)
                profile_complete = bool(profile.company_name)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'username': user.username,
                'role': user.role,
                'profile_complete': profile_complete
            })
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def job_category_list_create(request):
    if request.method == 'GET':
        job_categories = JobCategory.objects.all()
        serializer = JobCategorySerializer(job_categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = JobCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def job_category_detail(request, pk):
    try:
        job_category = JobCategory.objects.get(pk=pk)
    except JobCategory.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        skills = job_category.skills.all()
        freelancers = User.objects.filter(role=User.Role.FREELANCER, skills__in=skills).distinct()

        response_data = {
            'job_category': JobCategorySerializer(job_category).data,
            'skills': SkillSerializer(skills, many=True).data,
            'freelancers': UserSerializer(freelancers, many=True).data
        }

        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def skill_list_create(request):
    if request.method == 'GET':
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
       
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SkillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def skill_detail(request, pk):
    try:
        skill = Skill.objects.get(pk=pk)
    except Skill.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    freelancers = User.objects.filter(role=User.Role.FREELANCER, freelancer_profile__skills=skill).distinct()
    
    serializer = UserSerializer(freelancers, many=True)
    return Response({
        'skill': SkillSerializer(skill).data,
        'freelancers': serializer.data
    })


@api_view(['GET'])
def skill_freelancers(request, pk):
    
    try:
       
        skill = Skill.objects.get(pk=pk)
    except Skill.DoesNotExist:
        
        return Response({'detail': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

    
    freelancers = User.objects.filter(role=User.Role.FREELANCER, skills=skill).distinct()

    
    serializer = UserSerializer(freelancers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


""" JOB APPLICATIONS VIEWS"""

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def job_create(request):
    if request.method == 'POST':
        
        job_categories = JobCategory.objects.all()
        job_category_serializer = JobCategorySerializer(job_categories, many=True)

        
        category_id = request.data.get('category')
        if category_id:
            try:
                category = JobCategory.objects.get(id=category_id)
                related_skills = category.skills.all()
                skill_serializer = SkillSerializer(related_skills, many=True)
            except JobCategory.DoesNotExist:
                return Response({'detail': 'Invalid job category'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            skill_serializer = SkillSerializer(Skill.objects.all(), many=True)

       
        serializer = JobSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(client=request.user)
            return Response({
                'job': serializer.data,
                'categories': job_category_serializer.data,
                'skills': skill_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])

def job_list(request):
    jobs = Job.objects.all().order_by('-created_at')
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)


@api_view(['GET'])

def job_list_filtered(request):
    jobs = Job.objects.all()

    category = request.query_params.get('category')
    if category:
        jobs = jobs.filter(category__id=category)

    skill = request.query_params.get('skill')
    if skill:
        jobs = jobs.filter(required_skills__id=skill)

    min_pay = request.query_params.get('minPay')
    max_pay = request.query_params.get('maxPay')
    if min_pay:
        jobs = jobs.filter(pay__gte=min_pay)
    if max_pay:
        jobs = jobs.filter(pay__lte=max_pay)

    jobs = jobs.order_by('-created_at')

    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)

import logging
import traceback

logger = logging.getLogger(__name__)


@api_view(['GET', 'PUT', 'DELETE'])
def job_detail(request, pk):
    logger.info(f"Attempting to retrieve job with pk: {pk}")
    try:
        job = Job.objects.get(pk=pk)
        logger.info(f"Job found: {job}")
    except Job.DoesNotExist:
        logger.warning(f"Job with pk {pk} not found")
        return Response({'detail': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Unexpected error in job_detail view: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({'detail': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if request.method == 'GET':
        try:
            serializer = JobSerializer(job)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error serializing job data: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({'detail': 'Error processing job data'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PUT':
        if request.user != job.client:
            return Response({'detail': 'You do not have permission to edit this job.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = JobSerializer(job, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if request.user != job.client:
            return Response({'detail': 'You do not have permission to delete this job.'}, status=status.HTTP_403_FORBIDDEN)

        job.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET', 'POST'])
def apply_for_job(request, job_id):
    if request.method == 'GET':
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        applications = JobApplication.objects.filter(job=job)
        serializer = JobApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        user = request.user
        data = request.data.copy()  #
        data['job'] = job_id
        data['user'] = user.id

        serializer = JobApplicationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_jobs_list(request):
    if request.user.role != User.Role.CLIENT:
        return Response({'detail': 'You do not have permission to view this.'}, status=status.HTTP_403_FORBIDDEN)

    jobs = Job.objects.filter(client=request.user)
    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_job_applications(request):
    applications = JobApplication.objects.filter(user=request.user).select_related('job')
    serializer = JobApplicationSerializer(applications, many=True)
    return Response(serializer.data)




@api_view(['GET'])
def job_applications_list(request, job_pk):
    try:
        job = Job.objects.get(pk=job_pk)
    except Job.DoesNotExist:
        return Response({'detail': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)

    applications = JobApplication.objects.filter(job=job)
    serializer = JobApplicationSerializer(applications, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


""" SEARCH FUNCTIONALITY"""

@api_view(['GET', 'POST'])
def search_view(request):
    if request.method == 'GET':
        
        keyword = request.query_params.get('q', None)
    elif request.method == 'POST':
        
        keyword = request.data.get('q', None)
    else:
        return Response({'detail': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if not keyword:
        return Response({'detail': 'Please provide a search keyword.'}, status=status.HTTP_400_BAD_REQUEST)

    
    jobs = Job.objects.filter(
        Q(title__icontains=keyword) |
        Q(description__icontains=keyword) |
        Q(category__name__icontains=keyword) |
        Q(required_skills__name__icontains=keyword)
    ).distinct()
    job_serializer = JobSerializer(jobs, many=True)

    
    skills = Skill.objects.filter(
        Q(name__icontains=keyword)
    ).distinct()
    skill_serializer = SkillSerializer(skills, many=True)

    
    freelancers = User.objects.filter(
        Q(role=User.Role.FREELANCER),
        Q(username__icontains=keyword) |
        Q(skills__name__icontains=keyword) |
        Q(freelancerprofile__bio__icontains=keyword)
    ).distinct()
    freelancer_serializer = UserSerializer(freelancers, many=True)

    
    job_categories = JobCategory.objects.filter(
        Q(name__icontains=keyword)
    ).distinct()
    job_category_serializer = JobCategorySerializer(job_categories, many=True)

    
    results = {
        'jobs': job_serializer.data,
        'skills': skill_serializer.data,
        'freelancers': freelancer_serializer.data,
        'job_categories': job_category_serializer.data,
    }

    return Response(results, status=status.HTTP_200_OK)



@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def update_client_profile(request):
    try:
        profile = ClientProfile.objects.get(user=request.user)
    except ClientProfile.DoesNotExist:
        profile = ClientProfile(user=request.user)

    if request.method == 'GET':
        serializer = ClientProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ClientProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





@api_view(['GET'])
def filtered_freelancers(request):
    category_id = request.query_params.get('category')

    if not category_id or category_id == 'undefined':
        return Response({"error": "Valid category ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        category_id = int(category_id)
    except ValueError:
        return Response({"error": "Invalid category ID"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = JobCategory.objects.get(id=category_id)
    except JobCategory.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    freelancers = FreelancerProfile.objects.filter(job_categories=category).select_related('user').prefetch_related('skills', 'job_categories')
    for freelancer in freelancers:
        print(f"Freelancer: {freelancer.user.username}")
        print(f"Skills: {list(freelancer.skills.values('id', 'name'))}")
        print(f"Job Categories: {list(freelancer.job_categories.values('id', 'name'))}")

    serializer = FreelancerProfileDetailSerializer(freelancers, many=True)
    return Response(serializer.data)



@api_view(['GET'])
def freelancer_detail(request, pk):
    try:
        freelancer = FreelancerProfile.objects.get(pk=pk)
    except FreelancerProfile.DoesNotExist:
        return Response(status=404)

    serializer = FreelancerProfileDetailSerializer(freelancer)
    return Response(serializer.data)

@api_view(['GET'])
def freelancer_list(request):
    freelancers = FreelancerProfile.objects.all()
    serializer = FreelancerProfileSerializer(freelancers, many=True)
    return Response(serializer.data)



@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def update_freelancer_profile(request):
    try:
        profile = FreelancerProfile.objects.get(user=request.user)
    except FreelancerProfile.DoesNotExist:
        profile = FreelancerProfile.objects.create(user=request.user)

    if request.method == 'GET':
        serializer = FreelancerProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = FreelancerProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            
            error_messages = {}
            for field, errors in serializer.errors.items():
                error_messages[field] = str(errors[0])
            return Response({"errors": error_messages}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])

def freelancer_list(request):
    
    freelancers = User.objects.filter(role=User.Role.FREELANCER)

    
    skill_id = request.query_params.get('skill')
    if skill_id:
        try:
            skill = Skill.objects.get(id=skill_id)
            freelancers = freelancers.filter(skills=skill)
        except Skill.DoesNotExist:
            return Response({'detail': 'Skill not found'}, status=status.HTTP_404_NOT_FOUND)

    

    
    serializer = UserSerializer(freelancers, many=True)

   
    freelancer_profiles = FreelancerProfile.objects.filter(user__in=freelancers)
    profile_serializer = FreelancerProfileSerializer(freelancer_profiles, many=True)

    
    combined_data = []
    for user, profile in zip(serializer.data, profile_serializer.data):
        combined_data.append({**user, 'profile': profile})

    return Response(combined_data)

@api_view(['GET'])

def skill_list(request):
    skills = Skill.objects.all()
    serializer = SkillSerializer(skills, many=True)
    return Response(serializer.data)