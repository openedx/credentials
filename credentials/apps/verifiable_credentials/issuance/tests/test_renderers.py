from django.test import TestCase

from ..renderers import JSONLDRenderer


class JSONLDRendererTestCase(TestCase):
    def setUp(self):
        self.renderer = JSONLDRenderer()

    def test_render(self):
        data = {
            "name": "Test Name",
            "age": None,
            "context": "test_context",
        }
        expected_output = '{"name":"Test Name","@context":"test_context"}'
        rendered_output = self.renderer.render(data)
        self.assertEqual(rendered_output, expected_output)
