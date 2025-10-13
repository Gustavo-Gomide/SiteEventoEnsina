# from django.core.management.base import BaseCommand, CommandError

# from usuarios import generator


# class Command(BaseCommand):
#     help = 'Generate certificates for validated inscriptions.'

#     def add_arguments(self, parser):
#         parser.add_argument('--evento', type=int, help='ID of the event to generate certificates for')

#     def handle(self, *args, **options):
#         evento_id = options.get('evento')
#         try:
#             if evento_id:
#                 generated = generator.generate_certificates_for_event(evento_id)
#             else:
#                 from eventos.models import Evento
#                 generated = 0
#                 for ev in Evento.objects.all():
#                     generated += generator.generate_certificates_for_event(ev.id)
#         except ImportError:
#             raise CommandError('Missing image/pdf generation libraries. Install Pillow, qrcode, reportlab')

#         self.stdout.write(self.style.SUCCESS(f'Generated {generated} certificates'))
