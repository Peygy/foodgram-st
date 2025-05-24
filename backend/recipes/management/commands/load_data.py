import os
import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = 'Load initial ingredients data into database'

    def handle(self, *args, **options):
        data_file = os.path.join('/app', 'data', 'ingredients.csv')

        if not os.path.exists(data_file):
            self.stdout.write(self.style.ERROR(f'File {data_file} not found!'))
            return

        self.stdout.write(self.style.SUCCESS(f'Loading ingredients from {data_file}...'))

        Ingredient.objects.all().delete()

        with open(data_file, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            created_count = 0
            for row in reader:
                if len(row) >= 2:
                    name, measurement_unit = row[0].strip(), row[1].strip()
                    if name and measurement_unit:
                        Ingredient.objects.get_or_create(
                            name=name,
                            measurement_unit=measurement_unit
                        )
                        created_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'Successfully loaded {created_count} ingredients')
            )