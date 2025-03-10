# Generated by Django 5.1.6 on 2025-02-25 07:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='deposit_amount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='installment_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='installment_plan',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_type',
            field=models.CharField(default='full', max_length=50),
        ),
    ]
