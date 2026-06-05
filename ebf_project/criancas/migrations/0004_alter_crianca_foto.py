from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criancas', '0003_crianca_foto'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crianca',
            name='foto',
            field=models.ImageField(null=True, upload_to='criancas/fotos/'),
        ),
    ]
