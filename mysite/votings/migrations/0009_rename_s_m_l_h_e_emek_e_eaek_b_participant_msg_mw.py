# Generated by Django 4.2.1 on 2024-07-22 23:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('votings', '0008_rename_result_voting_msg_voting_summary_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='participant',
            old_name='s_m_l_h_e_emek_e_eaek_b',
            new_name='msg_mw',
        ),
    ]
