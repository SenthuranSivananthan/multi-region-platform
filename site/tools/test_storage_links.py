"""Check storage guidance links and compatibility anchors after section changes."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("site_build", ROOT / "site" / "build.py")
site_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_build)


class StorageLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, body = site_build.read_front_matter(ROOT / "content" / "storage-across-regions.md")
        store = []
        cls.rendered = site_build.postprocess(
            site_build.expand_raw(site_build.render_md(body, store), store))

    def test_fragment_targets_exist_and_are_unique(self):
        ids = re.findall(r'\bid="([^"]+)"', self.rendered)
        self.assertEqual(len(ids), len(set(ids)))
        for target in re.findall(r'href="#([^"]+)"', self.rendered):
            with self.subTest(target=target):
                self.assertIn(target, ids)

    def test_priority_options_link_to_current_patterns(self):
        links = re.findall(r'<a href="#([^"]+)">([^<]+)</a>', self.rendered)
        for label, target, count in (
                ("GZRS with Geo-Priority Replication", "storage-pattern-1", 4),
                ("RA-GZRS with Geo-Priority Replication", "storage-pattern-1", 4),
                ("GRS with Geo-Priority Replication", "storage-pattern-1", 2),
                ("Blob Object Replication with Priority", "storage-pattern-2", 2)):
            with self.subTest(label=label):
                self.assertEqual([href for href, text in links if text == label], [target] * count)

    def test_legacy_fragments_land_at_section_headings(self):
        for alias, target in (
                ("paired-region-options", "platform-native-geo-replication"),
                ("high-availability", "high-availability-scenarios"),
                ("disaster-recovery", "disaster-recovery-scenarios"),
                ("evaluate-native-storage-data-replication-options", "replication-patterns"),
                ("geo-priority-eligibility", "storage-pattern-1"),
                ("priority-replication-eligibility", "storage-pattern-2"),
                ("evaluate-custom-replication", "storage-pattern-3"),
                ("evaluate-product-specific-replication", "storage-pattern-5"),
                ("databricks", "storage-pattern-5"),
                ("evaluate-azure-storage-partners", "azure-storage-partners")):
            with self.subTest(alias=alias):
                after = self.rendered.split(f'<a id="{alias}"></a>', 1)[1]
                self.assertRegex(after, rf'^(?:\s|</?p>|<a id="[^"]+"></a>)*<h[23] id="{target}">')

    def test_backup_fragments_land_at_callout_titles(self):
        for alias, title in (
                ("complement-replication-with-isolated-backup", "Complement replication with isolated backup"),
                ("region-of-choice-backup-preview", "Complement replication with isolated backup"),
                ("operational-backup-for-blobs", "Operational backup for blobs")):
            with self.subTest(alias=alias):
                after = self.rendered.split(f'<a id="{alias}"></a>', 1)[1]
                self.assertRegex(after, rf'^(?:\s|</?p>|<a id="[^"]+"></a>)*<strong>{title}</strong>')


if __name__ == "__main__":
    unittest.main()
