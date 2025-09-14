from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Setup initial users and groups for workflow'

    def handle(self, *args, **kwargs):
        # Create groups
        groups = ['FillerGroup1', 'FillerGroup2', 'FillerGroup3', 'ApproverGroup']
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)
            self.stdout.write(f'Created group: {group_name}')
        
        # Create users with groups
        users_data = [
            ('user1', 'user1@example.com', 'password123', 'FillerGroup1'),
            ('user2', 'user2@example.com', 'password123', 'FillerGroup2'),
            ('user3', 'user3@example.com', 'password123', 'FillerGroup3'),
            ('user4', 'user4@example.com', 'password123', 'ApproverGroup'),
        ]
        
        for username, email, password, group_name in users_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f'Created user: {username}')
            
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            self.stdout.write(f'Added {username} to {group_name}')
        
        # Create superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write('Created superuser: admin')
        
        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))