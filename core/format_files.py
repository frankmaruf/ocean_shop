import os
import subprocess
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Format all files inside the project.'

    def handle(self, *args, **options):
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.py'):
                    filename = os.path.join(root, file)
                    print('Formatting file using autopep8: ', filename)
                    subprocess.run(['autopep8', '--in-place', filename])
                elif file.endswith('.html'):
                    print('Formatting file using djLint: ', filename)
                    subprocess.run(
                        ['djlint', filename, '--profile=django'])
                else:
                    print('Skipping file: ', filename)