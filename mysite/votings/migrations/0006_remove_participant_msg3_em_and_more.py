# Generated by Django 4.2.1 on 2024-07-11 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('votings', '0005_alter_participant_s_m_l_h_e_emek_e_eaek_b'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participant',
            name='msg3_em',
        ),
        migrations.RemoveField(
            model_name='participant',
            name='s_m_msg4_ma',
        ),
        migrations.AddField(
            model_name='participant',
            name='s_m_l_rfp_and_l_e_eaek_b',
            field=models.BinaryField(default=None, null=True),
        ),
    ]
