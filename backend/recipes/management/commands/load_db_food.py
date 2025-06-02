import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--path", type=str)

    def handle(self, *args, **options):
        file_path = options["path"] + "ingredients.csv"

        existing_ingredients = set(
            Ingredient.objects.values_list(
                'name',
                'measurement_unit',
            )
        )

        ingredients_to_create = []
        with open(file_path, "r") as csv_file:
            reader = csv.reader(csv_file)

            for row in reader:
                name = row[0].strip()
                unit = row[1].strip()

                if (name, unit) not in existing_ingredients:
                    ingredients_to_create.append(
                        Ingredient(name=name, measurement_unit=unit)
                    )
                else:
                    print(f"Ингредиент '{name} ({unit})'"
                          f"уже есть в базе данных")

        if ingredients_to_create:
            created_count = len(
                Ingredient.objects.bulk_create(
                    ingredients_to_create,
                )
            )
            print(f"Добавлено {created_count} новых ингредиентов")
