from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from chat.models import ChatMessage

class Command(BaseCommand):
    help = 'Nukes chat messages older than 24 hours to clear orphaned data.'

    def handle(self, *args, **kwargs):
        threshold = timezone.now() - timedelta(hours=24)
        
        orphaned_messages = ChatMessage.objects.filter(created_at__lt=threshold)
        count, _ = orphaned_messages.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Garbage Collector Run: Nuked {count} old messages.'))