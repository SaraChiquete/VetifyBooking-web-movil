from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

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
from .serializers import (
    AppointmentSerializer,
    PetSerializer,
    ServiceSerializer,
    VeterinarianSerializer,
    ClinicScheduleSerializer,
    DocumentSerializer,
    UserProfileSerializer,
    MedicalConsultationSerializer,
    MedicalPrescriptionSerializer,
    PrescriptionItemSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """Login app móvil con correo (o username legacy). Devuelve token + user_id."""
    password = request.data.get('password')
    email = (request.data.get('email') or '').strip()
    username = (request.data.get('username') or '').strip()

    if not password:
        return Response(
            {'detail': 'La contraseña es obligatoria.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = None
    if email:
        cuenta = User.objects.filter(email__iexact=email).first()
        if cuenta is not None:
            user = authenticate(
                request, username=cuenta.username, password=password
            )
    elif username:
        user = authenticate(
            request, username=username, password=password
        )
    else:
        return Response(
            {'detail': 'Indica tu correo electrónico y contraseña.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if user is None:
        return Response(
            {'detail': 'Correo o contraseña incorrectos.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user_id': user.pk})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """Alta de usuario para la app móvil; devuelve token para entrar directo."""
    username = (request.data.get('username') or '').strip()
    email = (request.data.get('email') or '').strip()
    password = request.data.get('password') or ''
    password2 = (
        request.data.get('password_confirm')
        or request.data.get('password2')
        or ''
    )
    phone = (request.data.get('phone') or '').strip()
    first_name = (request.data.get('first_name') or '').strip()

    errors = {}
    if not username:
        errors['username'] = ['Este campo es obligatorio.']
    if not email:
        errors['email'] = ['Este campo es obligatorio.']
    if not password:
        errors['password'] = ['Este campo es obligatorio.']
    if password != password2:
        errors['password_confirm'] = ['Las contraseñas no coinciden.']
    if len(password) < 8:
        errors['password'] = ['La contraseña debe tener al menos 8 caracteres.']
    if User.objects.filter(username__iexact=username).exists():
        errors['username'] = ['Ese nombre de usuario ya está en uso.']
    if User.objects.filter(email__iexact=email).exists():
        errors['email'] = ['Ese correo ya está registrado.']
    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name or username,
    )
    if phone:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.phone = phone
        profile.save()

    token, _ = Token.objects.get_or_create(user=user)
    return Response(
        {'token': token.key, 'user_id': user.pk},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def mi_cuenta(request):
    """Perfil del usuario autenticado (RF-02 app móvil)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'GET':
        return Response({
            'profile_id': profile.pk,
            'username': request.user.username,
            'first_name': request.user.first_name or '',
            'email': request.user.email or '',
            'phone': profile.phone or '',
            'address': profile.address or '',
        })
    first_name = (request.data.get('first_name') or '').strip()
    email = (request.data.get('email') or '').strip()
    phone = request.data.get('phone')
    address = request.data.get('address')
    if email:
        request.user.email = email
    if first_name:
        request.user.first_name = first_name
    request.user.save()
    profile.phone = (str(phone).strip() if phone is not None else '') or None
    profile.address = (str(address).strip() if address is not None else '') or None
    profile.save()
    return Response({
        'profile_id': profile.pk,
        'username': request.user.username,
        'first_name': request.user.first_name,
        'email': request.user.email,
        'phone': profile.phone or '',
        'address': profile.address or '',
    })


# PETS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def mascotas_lista(request):
    if request.method == 'GET':
        mascotas = Pet.objects.filter(owner=request.user)
        serializer = PetSerializer(mascotas, many=True)
        return Response(serializer.data)

    serializer = PetSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def mascota_detalle(request, pk):
    mascota = get_object_or_404(Pet, pk=pk, owner=request.user)

    if request.method == 'GET':
        serializer = PetSerializer(mascota)
        return Response(serializer.data)

    if request.method in ('PUT', 'PATCH'):
        partial = request.method == 'PATCH'
        serializer = PetSerializer(
            mascota, data=request.data, partial=partial
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    mascota.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# APPOINTMENTS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def citas_lista(request):
    if request.method == 'GET':
        citas = Appointment.objects.filter(user=request.user)
        serializer = AppointmentSerializer(citas, many=True)
        return Response(serializer.data)

    serializer = AppointmentSerializer(
        data=request.data, context={'request': request}
    )
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def cita_detalle(request, pk):
    cita = get_object_or_404(Appointment, pk=pk, user=request.user)

    if request.method == 'GET':
        serializer = AppointmentSerializer(cita)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = AppointmentSerializer(
            cita, data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    cita.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# SERVICES
@api_view(['GET', 'POST'])
def servicios_lista(request):
    if request.method == 'GET':
        servicios = Service.objects.all()
        serializer = ServiceSerializer(servicios, many=True)
        return Response(serializer.data)

    serializer = ServiceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def servicio_detalle(request, pk):
    servicio = get_object_or_404(Service, pk=pk)

    if request.method == 'GET':
        serializer = ServiceSerializer(servicio)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ServiceSerializer(servicio, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    servicio.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# VETERINARIANS
@api_view(['GET', 'POST'])
def veterinarios_lista(request):
    if request.method == 'GET':
        veterinarios = Veterinarian.objects.all()
        serializer = VeterinarianSerializer(veterinarios, many=True)
        return Response(serializer.data)

    serializer = VeterinarianSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def veterinario_detalle(request, pk):
    veterinario = get_object_or_404(Veterinarian, pk=pk)

    if request.method == 'GET':
        serializer = VeterinarianSerializer(veterinario)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = VeterinarianSerializer(veterinario, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    veterinario.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# CLINIC SCHEDULES
@api_view(['GET', 'POST'])
def horarios_lista(request):
    if request.method == 'GET':
        horarios = ClinicSchedule.objects.all()
        serializer = ClinicScheduleSerializer(horarios, many=True)
        return Response(serializer.data)

    serializer = ClinicScheduleSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def horario_detalle(request, pk):
    horario = get_object_or_404(ClinicSchedule, pk=pk)

    if request.method == 'GET':
        serializer = ClinicScheduleSerializer(horario)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ClinicScheduleSerializer(horario, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    horario.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# DOCUMENTS
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def documentos_lista(request):
    if request.method == 'GET':
        documentos = Document.objects.all()
        serializer = DocumentSerializer(documentos, many=True)
        return Response(serializer.data)

    serializer = DocumentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def documento_detalle(request, pk):
    documento = get_object_or_404(Document, pk=pk)

    if request.method == 'GET':
        serializer = DocumentSerializer(documento)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = DocumentSerializer(documento, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(documento.errors, status=status.HTTP_400_BAD_REQUEST)

    documento.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# USER PROFILES
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def perfiles_lista(request):
    if request.method == 'GET':
        perfiles = UserProfile.objects.filter(user=request.user)
        serializer = UserProfileSerializer(perfiles, many=True)
        return Response(serializer.data)

    serializer = UserProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def perfil_detalle(request, pk):
    perfil = get_object_or_404(UserProfile, pk=pk, user=request.user)

    if request.method == 'GET':
        serializer = UserProfileSerializer(perfil)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = UserProfileSerializer(perfil, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(perfil.errors, status=status.HTTP_400_BAD_REQUEST)

    perfil.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# MEDICAL CONSULTATIONS
@api_view(['GET', 'POST'])
def consultas_lista(request):
    if request.method == 'GET':
        consultas = MedicalConsultation.objects.filter(
            appointment__user=request.user
        )
        serializer = MedicalConsultationSerializer(consultas, many=True)
        return Response(serializer.data)

    serializer = MedicalConsultationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def consulta_detalle(request, pk):
    consulta = get_object_or_404(MedicalConsultation, pk=pk)

    if request.method == 'GET':
        serializer = MedicalConsultationSerializer(consulta)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = MedicalConsultationSerializer(consulta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    consulta.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# MEDICAL PRESCRIPTIONS
@api_view(['GET', 'POST'])
def recetas_lista(request):
    if request.method == 'GET':
        recetas = MedicalPrescription.objects.all()
        serializer = MedicalPrescriptionSerializer(recetas, many=True)
        return Response(serializer.data)

    serializer = MedicalPrescriptionSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def receta_detalle(request, pk):
    receta = get_object_or_404(MedicalPrescription, pk=pk)

    if request.method == 'GET':
        serializer = MedicalPrescriptionSerializer(receta)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = MedicalPrescriptionSerializer(receta, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    receta.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# PRESCRIPTION ITEMS
@api_view(['GET', 'POST'])
def medicamentos_receta_lista(request):
    if request.method == 'GET':
        items = PrescriptionItem.objects.all()
        serializer = PrescriptionItemSerializer(items, many=True)
        return Response(serializer.data)

    serializer = PrescriptionItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def medicamento_receta_detalle(request, pk):
    item = get_object_or_404(PrescriptionItem, pk=pk)

    if request.method == 'GET':
        serializer = PrescriptionItemSerializer(item)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = PrescriptionItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    item.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
