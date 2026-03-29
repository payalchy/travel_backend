import pandas as pd
from django.core.management.base import BaseCommand
from recommendation.models import Destination

class Command(BaseCommand): 
    help = 'Import places from Excel file'

    def handle(self, *args, **kwargs):
        df = pd.read_excel('real_nepal_4000_destinations_final.xlsx')

        for _, row in df.iterrows():
            Destination.objects.get_or_create(
                pName=row['pName'],
                province=row['province'],
                defaults={
                    'culture': row.get('culture', 0) if pd.notna(row.get('culture')) else 0,
                    'adventure': row.get('adventure', 0) if pd.notna(row.get('adventure')) else 0,
                    'wildlife': row.get('wildlife', 0) if pd.notna(row.get('wildlife')) else 0,
                    'sightseeing': row.get('sightseeing', 0) if pd.notna(row.get('sightseeing')) else 0,
                    'history': row.get('history', 0) if pd.notna(row.get('history')) else 0,
                    'tags': row.get('tags', '') if pd.notna(row.get('tags')) else '',
                }
            )

        self.stdout.write(self.style.SUCCESS('Data imported successfully!'))