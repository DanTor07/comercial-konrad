from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_pedido_comision_pedido_envio_pedido_iva_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoria',
            name='domicilio_base',
            field=models.FloatField(default=10000, help_text='Costo base de domicilio para esta categoría'),
        ),
        migrations.AddField(
            model_name='categoria',
            name='porcentaje_iva',
            field=models.FloatField(default=0.19, help_text='Porcentaje de IVA (ej. 0.19)'),
        ),
        migrations.AlterField(
            model_name='categoria',
            name='porcentaje_comision',
            field=models.FloatField(help_text='Porcentaje de comisión (ej. 0.1 para 10%)'),
        ),
    ]
