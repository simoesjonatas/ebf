from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criancas', '0002_alter_crianca_autorizacao_imagem'),
    ]

    operations = [
        migrations.AddField(
            model_name='crianca',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='criancas/fotos/'),
        ),
    ]
