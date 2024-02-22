import csv

from django.core.management.base import BaseCommand

from ...models import Ingredient, Tag


def import_data():
    with open('../data/ingredients.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        create_ingredients = [
            Ingredient(
                name=row['name'],
                measurement_unit=row['measurement_unit'],
            )
            for row in reader
        ]
        Ingredient.objects.bulk_create(
            create_ingredients
        )

    with open('../data/tags.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            Tag.objects.create(
                name=row['name'],
                color=row['color'],
                slug=row['slug'],
            )


class Command(BaseCommand):
    help = 'Import CSV data into db'

    def handle(self, *args, **options):
        import_data()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
