from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from knowledge_app.models import CustomMap, CustomNode, CustomEdge
import json


class CustomMapTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.other_user = User.objects.create_user(username='otheruser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.custom_map = CustomMap.objects.create(user=self.user, title='Test Map')

    # -------------------------------------------------------------------------
    # Homepage / map builder
    # -------------------------------------------------------------------------

    def test_homepage_loads(self):
        """Homepage should load successfully for logged in user."""
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_uses_correct_template(self):
        """Homepage should use the homepage template."""
        response = self.client.get(reverse('homepage'))
        self.assertTemplateUsed(response, 'knowledge_app/homepage.html')

    def test_homepage_requires_login(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('homepage'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_homepage_creates_map_if_none_exists(self):
        """Visiting homepage with no maps should auto-create one."""
        CustomMap.objects.filter(user=self.user).delete()
        self.client.get(reverse('homepage'))
        self.assertEqual(CustomMap.objects.filter(user=self.user).count(), 1)

    def test_homepage_loads_specific_map(self):
        """Visiting homepage with map_id should load that specific map."""
        response = self.client.get(reverse('homepage_map', args=[self.custom_map.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['custom_map'], self.custom_map)

    def test_homepage_map_returns_404_for_other_users_map(self):
        """Loading another user's map should return 404."""
        other_map = CustomMap.objects.create(user=self.other_user, title='Other Map')
        response = self.client.get(reverse('homepage_map', args=[other_map.id]))
        self.assertEqual(response.status_code, 404)

    def test_homepage_passes_nodes_to_template(self):
        """Homepage context should contain nodes."""
        response = self.client.get(reverse('homepage'))
        self.assertIn('nodes', response.context)

    def test_homepage_passes_edges_to_template(self):
        """Homepage context should contain edges."""
        response = self.client.get(reverse('homepage'))
        self.assertIn('edges', response.context)

    # -------------------------------------------------------------------------
    # New custom map
    # -------------------------------------------------------------------------

    def test_new_custom_map_creates_record(self):
        """Creating a new custom map should add a record to the database."""
        count_before = CustomMap.objects.filter(user=self.user).count()
        self.client.get(reverse('new_custom_map'))
        self.assertEqual(CustomMap.objects.filter(user=self.user).count(), count_before + 1)

    def test_new_custom_map_redirects_to_homepage_map(self):
        """Creating a new custom map should redirect to the map builder."""
        response = self.client.get(reverse('new_custom_map'))
        self.assertEqual(response.status_code, 302)
        new_map = CustomMap.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertRedirects(response, reverse('homepage_map', args=[new_map.id]))

    def test_new_custom_map_requires_login(self):
        """Unauthenticated users should be redirected to login."""
        self.client.logout()
        response = self.client.get(reverse('new_custom_map'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_new_custom_map_has_default_title(self):
        """New custom map should have the default title 'Untitled Map'."""
        self.client.get(reverse('new_custom_map'))
        new_map = CustomMap.objects.filter(user=self.user).order_by('-created_at').first()
        self.assertEqual(new_map.title, 'Untitled Map')

    # -------------------------------------------------------------------------
    # Add custom node
    # -------------------------------------------------------------------------

    def test_add_custom_node_creates_record(self):
        """POST to save_custom_node should create a CustomNode."""
        self.client.post(
            reverse('save_custom_node', args=[self.custom_map.id]),
            data=json.dumps({'label': 'Test Node', 'summary': 'Summary', 'x': 100, 'y': 200}),
            content_type='application/json'
        )
        self.assertEqual(CustomNode.objects.filter(custom_map=self.custom_map).count(), 1)

    def test_add_custom_node_returns_node_data(self):
        """POST to save_custom_node should return node id, label and summary."""
        response = self.client.post(
            reverse('save_custom_node', args=[self.custom_map.id]),
            data=json.dumps({'label': 'Test Node', 'summary': 'Summary', 'x': 100, 'y': 200}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertEqual(data['label'], 'Test Node')

    def test_add_custom_node_without_label_returns_400(self):
        """POST without a label should return 400."""
        response = self.client.post(
            reverse('save_custom_node', args=[self.custom_map.id]),
            data=json.dumps({'label': '', 'summary': 'Summary', 'x': 0, 'y': 0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_add_custom_node_to_other_users_map_returns_404(self):
        """Adding a node to another user's map should return 404."""
        other_map = CustomMap.objects.create(user=self.other_user, title='Other Map')
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('save_custom_node', args=[self.custom_map.id]),
            data=json.dumps({'label': 'Test', 'summary': '', 'x': 0, 'y': 0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    def test_add_custom_node_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.post(
            reverse('save_custom_node', args=[self.custom_map.id]),
            data=json.dumps({'label': 'Test', 'summary': '', 'x': 0, 'y': 0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    # -------------------------------------------------------------------------
    # Update custom node position
    # -------------------------------------------------------------------------

    def test_update_custom_node_position(self):
        """POST to update_custom_node_position should update x and y."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        self.client.post(
            reverse('update_custom_node_position', args=[self.custom_map.id, node.id]),
            data=json.dumps({'x': 150, 'y': 250}),
            content_type='application/json'
        )
        node.refresh_from_db()
        self.assertEqual(node.x_position, 150)
        self.assertEqual(node.y_position, 250)

    def test_update_custom_node_position_returns_success(self):
        """POST to update_custom_node_position should return success."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        response = self.client.post(
            reverse('update_custom_node_position', args=[self.custom_map.id, node.id]),
            data=json.dumps({'x': 150, 'y': 250}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    # -------------------------------------------------------------------------
    # Delete custom node
    # -------------------------------------------------------------------------

    def test_delete_custom_node_removes_from_database(self):
        """POST to delete_custom_node should remove the node."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        self.client.post(reverse('delete_custom_node', args=[self.custom_map.id, node.id]))
        self.assertFalse(CustomNode.objects.filter(id=node.id).exists())

    def test_delete_custom_node_returns_success(self):
        """POST to delete_custom_node should return success JSON."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        response = self.client.post(
            reverse('delete_custom_node', args=[self.custom_map.id, node.id])
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_delete_nonexistent_custom_node_returns_404(self):
        """Deleting a node that doesn't exist should return 404."""
        response = self.client.post(
            reverse('delete_custom_node', args=[self.custom_map.id, 9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_custom_node_from_other_users_map_returns_404(self):
        """Deleting a node from another user's map should return 404."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        self.client.login(username='otheruser', password='testpass123')
        response = self.client.post(
            reverse('delete_custom_node', args=[self.custom_map.id, node.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_custom_node_requires_login(self):
        """Unauthenticated users should be redirected."""
        node = CustomNode.objects.create(
            custom_map=self.custom_map, label='Node', summary='', x_position=0, y_position=0
        )
        self.client.logout()
        response = self.client.post(
            reverse('delete_custom_node', args=[self.custom_map.id, node.id])
        )
        self.assertEqual(response.status_code, 302)

    # -------------------------------------------------------------------------
    # Add custom edge
    # -------------------------------------------------------------------------

    def test_add_custom_edge_creates_record(self):
        """POST to save_custom_edge should create a CustomEdge."""
        node_a = CustomNode.objects.create(
            custom_map=self.custom_map, label='A', summary='', x_position=0, y_position=0
        )
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=100, y_position=100
        )
        self.client.post(
            reverse('save_custom_edge', args=[self.custom_map.id]),
            data=json.dumps({'source_id': node_a.id, 'target_id': node_b.id, 'label': 'connects'}),
            content_type='application/json'
        )
        self.assertEqual(CustomEdge.objects.filter(custom_map=self.custom_map).count(), 1)

    def test_add_custom_edge_returns_edge_data(self):
        """POST to save_custom_edge should return edge data."""
        node_a = CustomNode.objects.create(
            custom_map=self.custom_map, label='A', summary='', x_position=0, y_position=0
        )
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=100, y_position=100
        )
        response = self.client.post(
            reverse('save_custom_edge', args=[self.custom_map.id]),
            data=json.dumps({'source_id': node_a.id, 'target_id': node_b.id, 'label': 'connects'}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertEqual(data['source'], str(node_a.id))
        self.assertEqual(data['target'], str(node_b.id))

    def test_add_custom_edge_without_source_returns_400(self):
        """POST without source_id should return 400."""
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=0, y_position=0
        )
        response = self.client.post(
            reverse('save_custom_edge', args=[self.custom_map.id]),
            data=json.dumps({'target_id': node_b.id, 'label': 'connects'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_add_custom_edge_requires_login(self):
        """Unauthenticated users should be redirected."""
        self.client.logout()
        response = self.client.post(
            reverse('save_custom_edge', args=[self.custom_map.id]),
            data=json.dumps({'source_id': 1, 'target_id': 2, 'label': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 302)

    # -------------------------------------------------------------------------
    # Delete custom edge
    # -------------------------------------------------------------------------

    def test_delete_custom_edge_removes_from_database(self):
        """POST to delete_custom_edge should remove the edge."""
        node_a = CustomNode.objects.create(
            custom_map=self.custom_map, label='A', summary='', x_position=0, y_position=0
        )
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=0, y_position=0
        )
        edge = CustomEdge.objects.create(
            custom_map=self.custom_map, source=node_a, target=node_b, label='connects'
        )
        self.client.post(reverse('delete_custom_edge', args=[self.custom_map.id, edge.id]))
        self.assertFalse(CustomEdge.objects.filter(id=edge.id).exists())

    def test_delete_custom_edge_returns_success(self):
        """POST to delete_custom_edge should return success JSON."""
        node_a = CustomNode.objects.create(
            custom_map=self.custom_map, label='A', summary='', x_position=0, y_position=0
        )
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=0, y_position=0
        )
        edge = CustomEdge.objects.create(
            custom_map=self.custom_map, source=node_a, target=node_b, label='connects'
        )
        response = self.client.post(
            reverse('delete_custom_edge', args=[self.custom_map.id, edge.id])
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_delete_nonexistent_custom_edge_returns_404(self):
        """Deleting an edge that doesn't exist should return 404."""
        response = self.client.post(
            reverse('delete_custom_edge', args=[self.custom_map.id, 9999])
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_custom_edge_requires_login(self):
        """Unauthenticated users should be redirected."""
        node_a = CustomNode.objects.create(
            custom_map=self.custom_map, label='A', summary='', x_position=0, y_position=0
        )
        node_b = CustomNode.objects.create(
            custom_map=self.custom_map, label='B', summary='', x_position=0, y_position=0
        )
        edge = CustomEdge.objects.create(
            custom_map=self.custom_map, source=node_a, target=node_b, label='connects'
        )
        self.client.logout()
        response = self.client.post(
            reverse('delete_custom_edge', args=[self.custom_map.id, edge.id])
        )
        self.assertEqual(response.status_code, 302)

    # -------------------------------------------------------------------------
    # Update map title
    # -------------------------------------------------------------------------

    def test_update_custom_map_title(self):
        """POST to update_custom_map_title should update the title."""
        self.client.post(
            reverse('update_custom_map_title', args=[self.custom_map.id]),
            data=json.dumps({'title': 'New Title'}),
            content_type='application/json'
        )
        self.custom_map.refresh_from_db()
        self.assertEqual(self.custom_map.title, 'New Title')

    def test_update_custom_map_title_returns_success(self):
        """POST to update_custom_map_title should return success JSON."""
        response = self.client.post(
            reverse('update_custom_map_title', args=[self.custom_map.id]),
            data=json.dumps({'title': 'New Title'}),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_update_custom_map_title_empty_does_not_update(self):
        """Posting an empty title should not update the map title."""
        self.client.post(
            reverse('update_custom_map_title', args=[self.custom_map.id]),
            data=json.dumps({'title': ''}),
            content_type='application/json'
        )
        self.custom_map.refresh_from_db()
        self.assertEqual(self.custom_map.title, 'Test Map')

    def test_update_title_for_other_users_map_returns_404(self):
        """Updating another user's map title should return 404."""
        other_map = CustomMap.objects.create(user=self.other_user, title='Other Map')
        response = self.client.post(
            reverse('update_custom_map_title', args=[other_map.id]),
            data=json.dumps({'title': 'Hacked Title'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------------------
    # Maps page shows custom maps
    # -------------------------------------------------------------------------

    def test_maps_page_shows_custom_maps(self):
        """Maps page should show the user's custom maps."""
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'Test Map')

    def test_maps_page_shows_custom_maps_section(self):
        """Maps page should show the My Custom Maps heading."""
        response = self.client.get(reverse('maps'))
        self.assertContains(response, 'My Custom Maps')

    def test_maps_page_does_not_show_other_users_custom_maps(self):
        """Maps page should not show another user's custom maps."""
        CustomMap.objects.create(user=self.other_user, title='Other Custom Map')
        response = self.client.get(reverse('maps'))
        self.assertNotContains(response, 'Other Custom Map')
