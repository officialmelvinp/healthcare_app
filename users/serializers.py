from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PatientProfile, DoctorProfile

User = get_user_model()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PatientProfileSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = ['id', 'user', 'image', 'date_of_birth']
        read_only_fields = ['user']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.image.url)
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        return PatientProfile.objects.create(user=user, **validated_data)

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['id', 'user', 'specialization', 'availability']
        read_only_fields = ['user']

class UserProfileSerializer(serializers.ModelSerializer):
    patient_profile = PatientProfileSerializer(required=False)
    doctor_profile = DoctorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_patient', 'is_doctor', 'email_verified', 'patient_profile', 'doctor_profile']
        read_only_fields = ['is_patient', 'is_doctor', 'email_verified']

    def update(self, instance, validated_data):
        patient_profile_data = validated_data.pop('patient_profile', None)
        doctor_profile_data = validated_data.pop('doctor_profile', None)

        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create PatientProfile
        if instance.is_patient and patient_profile_data:
            PatientProfile.objects.update_or_create(user=instance, defaults=patient_profile_data)

        # Update or create DoctorProfile
        if instance.is_doctor and doctor_profile_data:
            DoctorProfile.objects.update_or_create(user=instance, defaults=doctor_profile_data)

        instance.refresh_from_db()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.is_patient:
            ret['patient_profile'] = PatientProfileSerializer(instance.patient_profile, context=self.context).data
        elif instance.is_doctor:
            ret['doctor_profile'] = DoctorProfileSerializer(instance.doctor_profile, context=self.context).data
        else:
            ret.pop('patient_profile', None)
            ret.pop('doctor_profile', None)
        return ret

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password_confirm = serializers.CharField(write_only=True, required=False)
    patient_profile = PatientProfileSerializer(required=False)
    doctor_profile = DoctorProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm', 
            'is_patient', 'is_doctor', 'email_verified', 'patient_profile', 'doctor_profile'
        ]
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'email_verified': {'read_only': True}
        }

    def validate(self, data):
        if 'password' in data and 'password_confirm' in data:
            if data['password'] != data['password_confirm']:
                raise serializers.ValidationError({"password": "Password fields didn't match."})
            if len(data['password']) < 8:
                raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        if data.get('is_patient') and data.get('is_doctor'):
            raise serializers.ValidationError("A user cannot be both a patient and a doctor.")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        patient_profile_data = validated_data.pop('patient_profile', None)
        doctor_profile_data = validated_data.pop('doctor_profile', None)
    
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data, email_verified=False)
        if password:
            user.set_password(password)
        user.save()

        if user.is_patient and patient_profile_data:
            PatientProfile.objects.create(user=user, **patient_profile_data)
        elif user.is_doctor and doctor_profile_data:
            DoctorProfile.objects.create(user=user, **doctor_profile_data)

        return user

    def update(self, instance, validated_data):
        validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        
        patient_profile_data = validated_data.pop('patient_profile', None)
        doctor_profile_data = validated_data.pop('doctor_profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instance.is_patient and patient_profile_data:
            PatientProfile.objects.update_or_create(user=instance, defaults=patient_profile_data)
        elif instance.is_doctor and doctor_profile_data:
            DoctorProfile.objects.update_or_create(user=instance, defaults=doctor_profile_data)

        instance.refresh_from_db()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.is_patient:
            ret['patient_profile'] = PatientProfileSerializer(instance.patient_profile, context=self.context).data
        elif instance.is_doctor:
            ret['doctor_profile'] = DoctorProfileSerializer(instance.doctor_profile, context=self.context).data
        else:
            ret.pop('patient_profile', None)
            ret.pop('doctor_profile', None)
        return ret

