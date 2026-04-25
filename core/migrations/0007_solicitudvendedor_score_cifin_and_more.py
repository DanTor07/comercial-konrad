from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_solicitudvendedor_tipo_persona_pedido_pedidoitem_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudvendedor',
            name='score_cifin',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='solicitudvendedor',
            name='score_datacredito',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='solicitudvendedor',
            name='tiene_antecedentes',
            field=models.BooleanField(default=False),
        ),
    ]
