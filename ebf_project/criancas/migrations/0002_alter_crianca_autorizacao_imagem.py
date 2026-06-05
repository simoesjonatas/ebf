from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criancas', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crianca',
            name='autorizacao_imagem',
            field=models.BooleanField(default=True),
        ),
    ]
