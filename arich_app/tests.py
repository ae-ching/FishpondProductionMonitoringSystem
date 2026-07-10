from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Fishpond, Harvest, FishType, FishpondFishType
from . import ml_loader


class MLLoaderTests(TestCase):
    def test_model_files_resolve_to_existing_artifacts(self):
        exists, missing = ml_loader.check_model_files_exist()
        self.assertTrue(exists, f"Expected model files to be found. Missing: {missing}")


class PaginationLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='secret123')

    def test_ponds_pagination_links_keep_search_and_status_params(self):
        for index in range(11):
            pond = Fishpond.objects.create(
                owner=self.user,
                name=f'Pond {index}',
                status='active' if index % 2 == 0 else 'maintenance',
            )
            fish_type = FishType.objects.create(user=self.user, name=f'Fish {index}')
            FishpondFishType.objects.create(pond=pond, fish_type=fish_type)

        self.client.force_login(self.user)
        response = self.client.get(reverse('ponds'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '?page=2&search=&status=')

    def test_harvest_pagination_links_keep_filter_params(self):
        pond = Fishpond.objects.create(owner=self.user, name='Harvest Pond', status='active')
        fish_type = FishType.objects.create(user=self.user, name='Tilapia')
        FishpondFishType.objects.create(pond=pond, fish_type=fish_type)

        for index in range(11):
            Harvest.objects.create(
                user=self.user,
                pond=pond,
                fish_type=fish_type,
                date='2024-01-01',
                quantity=5 + index,
            )

        self.client.force_login(self.user)
        response = self.client.get(reverse('harvest'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '?page=2&search=&pond=&fish=&start_date=&end_date=')

    def test_pond_action_buttons_target_existing_edit_and_delete_views(self):
        pond = Fishpond.objects.create(owner=self.user, name='Demo Pond', status='active')

        self.client.force_login(self.user)
        response = self.client.get(reverse('ponds'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-edit-url="{reverse("edit_fishpond", args=[pond.id])}"')
        self.assertContains(response, f'data-delete-url="{reverse("delete_fishpond", args=[pond.id])}"')
        self.assertContains(response, 'id="editFishpondModalOverlay"')
        self.assertContains(response, 'id="deleteFishpondModalOverlay"')

    def test_harvest_delete_action_uses_modal_overlay_and_delete_url(self):
        pond = Fishpond.objects.create(owner=self.user, name='Harvest Pond', status='active')
        fish_type = FishType.objects.create(user=self.user, name='Tilapia')
        FishpondFishType.objects.create(pond=pond, fish_type=fish_type)
        harvest = Harvest.objects.create(
            user=self.user,
            pond=pond,
            fish_type=fish_type,
            date='2024-01-01',
            quantity=5,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('harvest'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-delete-url="{reverse("delete_harvest", args=[harvest.id])}"')
        self.assertContains(response, 'id="deleteHarvestModalOverlay"')
        self.assertContains(response, 'id="deleteHarvestModalContent"')

    def test_delete_harvest_modal_request_renders_confirmation_fragment(self):
        pond = Fishpond.objects.create(owner=self.user, name='Harvest Pond', status='active')
        fish_type = FishType.objects.create(user=self.user, name='Tilapia')
        FishpondFishType.objects.create(pond=pond, fish_type=fish_type)
        harvest = Harvest.objects.create(
            user=self.user,
            pond=pond,
            fish_type=fish_type,
            date='2024-01-01',
            quantity=5,
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse('delete_harvest', args=[harvest.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Delete Harvest Record')
        self.assertContains(response, 'Yes, Delete Harvest Record')

    def test_home_view_handles_multiple_fish_types_without_crashing(self):
        pond = Fishpond.objects.create(owner=self.user, name='Dashboard Pond', status='active')
        tilapia = FishType.objects.create(user=self.user, name='Tilapia')
        pusit = FishType.objects.create(user=self.user, name='Pusit')
        FishpondFishType.objects.create(pond=pond, fish_type=tilapia)
        FishpondFishType.objects.create(pond=pond, fish_type=pusit)

        Harvest.objects.create(user=self.user, pond=pond, fish_type=tilapia, date='2026-06-29', quantity=70)
        Harvest.objects.create(user=self.user, pond=pond, fish_type=pusit, date='2026-06-29', quantity=40)

        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tilapia')
        self.assertContains(response, 'Pusit')

    def test_home_view_provides_latest_harvest_for_kpi_card(self):
        pond = Fishpond.objects.create(owner=self.user, name='Pond A', status='active')
        fish_type = FishType.objects.create(user=self.user, name='Tilapia')
        FishpondFishType.objects.create(pond=pond, fish_type=fish_type)
        harvest = Harvest.objects.create(
            user=self.user,
            pond=pond,
            fish_type=fish_type,
            date='2026-06-29',
            quantity=70,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['latest_harvest'], harvest)
        self.assertEqual(list(response.context['latest_harvests']), [harvest])

    def test_edit_harvest_modal_uses_fish_type_dropdown(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('harvest'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="fish_type" id="editHarvestFishType"')
