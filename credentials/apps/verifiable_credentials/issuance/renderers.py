"""
Verifiable credentials renderers.
"""

from rest_framework.renderers import JSONRenderer


class JSONLDRenderer(JSONRenderer):
    """
    Renderer which serializes to JSON.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a string.

        Addionally, updates `data` shape a bit to conform json-ld specs.
        """

        tweaked_data = self._tweak(data)
        return super().render(tweaked_data, accepted_media_type, renderer_context).decode("utf-8")

    def _tweak(self, data):
        """
        Shape `data` with JSON-LD specifics.
        """
        # exchange special symbols:
        data["@context"] = data.pop("context")

        # trim nullable values:
        dense_data = self._hide_nullables(data)

        return dense_data

    def _hide_nullables(self, sparse_data):
        """
        Traverse dictionaries and remove empty data.
        """
        for key, value in sparse_data.copy().items():
            if isinstance(value, dict):
                self._hide_nullables(value)
            if not value:
                del sparse_data[key]

        return sparse_data
