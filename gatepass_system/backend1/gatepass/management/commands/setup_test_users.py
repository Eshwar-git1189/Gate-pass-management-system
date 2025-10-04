from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from gatepass.models import Profile, Student, Parent
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates test users for each role in the gatepass system'

    def handle(self, *args, **options):
        self.stdout.write('Creating test users...')

        with transaction.atomic():
            # Create Warden
            warden_user = self._create_user('warden', 'Warden Test', 'warden@test.com')
            self._create_profile(warden_user, 'WARDEN')
            self.stdout.write(self.style.SUCCESS(f'Created warden user: {warden_user.username}'))

            # Create Security
            security_user = self._create_user('security', 'Security Test', 'security@test.com')
            self._create_profile(security_user, 'SECURITY')
            self.stdout.write(self.style.SUCCESS(f'Created security user: {security_user.username}'))

            # Create Students with existing parents
            parents = Parent.objects.all()
            for i, parent in enumerate(parents, 1):
                # Create user for parent if doesn't exist
                if not hasattr(parent, 'profile'):
                    parent_user = self._create_user(
                        f'parent{i}', 
                        parent.name, 
                        parent.email or f'parent{i}@test.com'
                    )
                    parent_profile = self._create_profile(parent_user, 'PARENT')
                    parent.profile = parent_profile
                    parent.save()
                    self.stdout.write(self.style.SUCCESS(f'Created parent user: {parent_user.username}'))

                # Create student linked to this parent
                student_user = self._create_user(
                    f'student{i}',
                    f'Student {i}',
                    f'student{i}@test.com'
                )
                student_profile = self._create_profile(student_user, 'STUDENT')
                student = Student.objects.create(
                    profile=student_profile,
                    roll_no=f'S{i:03d}'
                )
                student.parents.add(parent)
                self.stdout.write(self.style.SUCCESS(f'Created student user: {student_user.username}'))

        self.stdout.write(self.style.SUCCESS('Successfully created all test users'))

    def _create_user(self, username, full_name, email, password='test1234'):
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'User {username} already exists')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        return user

    def _create_profile(self, user, user_type):
        try:
            profile = Profile.objects.get(user=user)
            profile.user_type = user_type
            profile.save()
        except Profile.DoesNotExist:
            profile = Profile.objects.create(
                user=user,
                user_type=user_type
            )
        return profile