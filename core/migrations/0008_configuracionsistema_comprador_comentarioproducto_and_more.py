import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_solicitudvendedor_score_cifin_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('porcentaje_iva', models.FloatField(default=0.19)),
                ('costo_domicilio_base', models.FloatField(default=10000.0)),
                ('costo_domicilio_por_kg', models.FloatField(default=1000.0)),
            ],
        ),
        migrations.CreateModel(
            name='Comprador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombres', models.CharField(max_length=100)),
                ('apellidos', models.CharField(max_length=100)),
                ('numero_identificacion', models.CharField(max_length=20, unique=True)),
                ('correo_electronico', models.EmailField(max_length=254)),
                ('pais', models.CharField(max_length=100)),
                ('ciudad', models.CharField(max_length=100)),
                ('direccion', models.CharField(max_length=200)),
                ('telefono', models.CharField(max_length=20)),
                ('twitter', models.CharField(blank=True, max_length=100, null=True)),
                ('instagram', models.CharField(blank=True, max_length=100, null=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='comprador_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ComentarioProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('es_pregunta', models.BooleanField(default=False)),
                ('texto', models.TextField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('respuesta_vendedor', models.TextField(blank=True, null=True)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='core.producto')),
                ('comprador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.comprador')),
            ],
        ),
        migrations.CreateModel(
            name='CalificacionTransaccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntaje', models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')])),
                ('comentario', models.TextField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('pedido', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='calificacion', to='core.pedido')),
                ('vendedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.vendedor')),
                ('comprador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.comprador')),
            ],
        ),
    ]
