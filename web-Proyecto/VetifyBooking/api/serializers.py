from rest_framework import serializers
from booking.models import (
    Appointment,
    Pet,
    Service,
    Veterinarian,
    ClinicSchedule,
    Document,
    UserProfile,
    MedicalConsultation,
    MedicalPrescription,
    PrescriptionItem,
)


class PetSerializer(serializers.ModelSerializer):
    """owner lo asigna la vista; no debe enviarse en el POST."""

    class Meta:
        model = Pet
        fields = '__all__'
        read_only_fields = ('id', 'owner', 'created_at', 'updated_at')


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at')

    def validate_pet(self, pet):
        request = self.context.get('request')
        if request and pet.owner_id != request.user.id:
            raise serializers.ValidationError(
                'La mascota no pertenece a tu cuenta.'
            )
        return pet

    def validate(self, data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return data

        pet = data.get('pet') or (self.instance.pet if self.instance else None)
        date = data.get('date') or (self.instance.date if self.instance else None)
        time = data.get('time') or (self.instance.time if self.instance else None)
        vet = data.get('veterinarian')
        if vet is None and self.instance:
            vet = self.instance.veterinarian

        if pet and date and time and vet is not None:
            qs = Appointment.objects.filter(
                veterinarian=vet,
                date=date,
                time=time,
            ).exclude(status='cancelled')
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'non_field_errors': [
                        'Ese veterinario ya tiene una cita en ese horario.'
                    ]
                })

        if pet and date and time:
            qs = Appointment.objects.filter(
                user=request.user,
                pet=pet,
                date=date,
                time=time,
            ).exclude(status='cancelled')
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({
                    'non_field_errors': [
                        'Ya tienes una cita para esta mascota en ese horario.'
                    ]
                })

        return data


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class VeterinarianSerializer(serializers.ModelSerializer):
    get_specialty_display = serializers.SerializerMethodField()

    class Meta:
        model = Veterinarian
        fields = '__all__'

    def get_get_specialty_display(self, obj):
        return obj.get_specialty_display()


class ClinicScheduleSerializer(serializers.ModelSerializer):
    get_day_of_week_display = serializers.SerializerMethodField()

    class Meta:
        model = ClinicSchedule
        fields = '__all__'

    def get_get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class MedicalConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalConsultation
        fields = '__all__'


class MedicalPrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalPrescription
        fields = '__all__'


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'
