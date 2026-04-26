from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_configuracionsistema_comprador_comentarioproducto_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='comision',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pedido',
            name='envio',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pedido',
            name='iva',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='pedido',
            name='subtotal',
            field=models.FloatField(default=0.0),
        ),
    ]
