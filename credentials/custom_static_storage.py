from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


module_patterns = (
    ('*.js', (
        (
            r"""(^|;)\s*(?P<matched>(?P<prefix>import(\s*\*\s*as\s+\w+\s+|\s+\w+\s+|\s*{[\w,\s]*?}\s*)from\s*)['"](?P<url>.*?)['"])""",
            "%(prefix)s '%(url)s'",
        ),
    )),
)


def get_static_url(path):
    from django.contrib.staticfiles.storage import staticfiles_storage

    return staticfiles_storage.url(path)


class CustomStaticFilesStorage(ManifestStaticFilesStorage):
    """
    ManifestStaticFilesStorage with additional features:
    1. If you have a manifest files error, the page to render the error probably
    has the same error, and then you can't debug it. This returns the error
    string so one can see in the rendered html there was a problem
    2. Remove the sourcemap patterns, add javascript module support.
    """

    # ------ Temp until: https://code.djangoproject.com/ticket/33353#comment:11
    no_sourcemap_patterns = (
        ("*.css", (
            r"""(?P<matched>url\(['"]{0,1}\s*(?P<url>.*?)["']{0,1}\))""",
            (
                r"""(?P<matched>@import\s*["']\s*(?P<url>.*?)["'])""",
                """@import url("%(url)s")""",
            ),
        )),
    )
    patterns = no_sourcemap_patterns + module_patterns
    # ------
    # patterns = ManifestStaticFilesStorage.patterns + module_patterns

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except ValueError as e:
            return f"{name}.could_not_find_static_file_to_calc_manifest_hash, {e}"
