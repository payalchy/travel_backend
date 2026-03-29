from django.core.management.base import BaseCommand
from recommendation.models import Destination
from django.db.models import Count

class Command(BaseCommand):
    help = 'Remove duplicate destinations'

    def handle(self, *args, **kwargs):
        duplicates = (
            Destination.objects
            .values('pName', 'province')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        for d in duplicates:
            objs = Destination.objects.filter(
                pName=d['pName'],
                province=d['province']
            )
            objs.exclude(id=objs.first().id).delete()

        self.stdout.write(self.style.SUCCESS('Duplicates removed!'))