from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.mi_cuenta, name='mi-cuenta'),
    path('mascotas/', views.mascotas_lista, name='mascotas-lista'),
    path('mascotas/<int:pk>/', views.mascota_detalle, name='mascota-detalle'),
    path('citas/', views.citas_lista, name='citas-lista'),
    path('citas/<int:pk>/', views.cita_detalle, name='cita-detalle'),

    path('servicios/', views.servicios_lista, name='servicios-lista'),
    path('servicios/<int:pk>/', views.servicio_detalle, name='servicio-detalle'),

    path('veterinarios/', views.veterinarios_lista, name='veterinarios-lista'),
    path('veterinarios/<int:pk>/', views.veterinario_detalle, name='veterinario-detalle'),

    path('horarios/', views.horarios_lista, name='horarios-lista'),
    path('horarios/<int:pk>/', views.horario_detalle, name='horario-detalle'),

    path('documentos/', views.documentos_lista, name='documentos-lista'),
    path('documentos/<int:pk>/', views.documento_detalle, name='documento-detalle'),

    path('perfiles/', views.perfiles_lista, name='perfiles-lista'),
    path('perfiles/<int:pk>/', views.perfil_detalle, name='perfil-detalle'),

    path('consultas/', views.consultas_lista, name='consultas-lista'),
    path('consultas/<int:pk>/', views.consulta_detalle, name='consulta-detalle'),

    path('recetas/', views.recetas_lista, name='recetas-lista'),
    path('recetas/<int:pk>/', views.receta_detalle, name='receta-detalle'),

    path('medicamentos-receta/', views.medicamentos_receta_lista, name='medicamentos-receta-lista'),
    path('medicamentos-receta/<int:pk>/', views.medicamento_receta_detalle, name='medicamento-receta-detalle'),
]
