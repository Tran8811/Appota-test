import json
import os
import tempfile
import unittest

from kb.access import split_allowed
from kb.loader import load_docs, parse_file

USERS = {u["id"]: u for u in json.load(open("users.json", encoding="utf-8"))}
DOCS, ERRORS = load_docs("data")


def ids(docs):
    return {d["doc_id"] for d in docs}


def reasons(rejected):
    return {d["doc_id"]: r for d, r in rejected}


class TestLoader(unittest.TestCase):
    def test_all_sample_docs_valid(self):
        self.assertEqual(ERRORS, [])
        self.assertEqual(len(DOCS), 11)

    def test_missing_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "bad.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("---\ndoc_id: X\ntitle: T\n---\nnoi dung")
            with self.assertRaises(ValueError) as cm:
                parse_file(p)
            self.assertIn("thiếu trường", str(cm.exception))
            docs, errors = load_docs(tmp)
            self.assertEqual(docs, [])
            self.assertEqual(len(errors), 1)

    def test_bad_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "bad.md")
            with open(p, "w", encoding="utf-8") as f:
                f.write("---\ndoc_id: X\ntitle: T\ntopic: t\nscope: group\n"
                        "owner_unit: Appota Group\naccess_level: 1\n"
                        "status: draft\neffective_date: 2026-01-01\n---\nnoi dung")
            with self.assertRaises(ValueError):
                parse_file(p)


class TestAccess(unittest.TestCase):
    def test_archived_is_never_allowed(self):
        for u in USERS.values():
            allowed, rejected = split_allowed(DOCS, u)
            self.assertNotIn("LEAVE-GROUP-v1", ids(allowed))
            self.assertEqual(reasons(rejected)["LEAVE-GROUP-v1"], "đã hết hiệu lực")

    def test_an_sees_company_b_not_company_c_or_it(self):
        allowed, _ = split_allowed(DOCS, USERS["an"])
        got = ids(allowed)
        self.assertIn("LEAVE-CTYB-v1", got)
        self.assertIn("LEAVE-GROUP-v2", got)
        self.assertIn("OT-MKT-v1", got)
        self.assertNotIn("IT-LAPTOP-v1", got)

    def test_binh_does_not_see_company_b_docs(self):
        allowed, rejected = split_allowed(DOCS, USERS["binh"])
        got = ids(allowed)
        self.assertIn("LEAVE-GROUP-v2", got)
        self.assertIn("IT-LAPTOP-v1", got)
        for forbidden in ("LEAVE-CTYB-v1", "OT-MKT-v1", "DISC-CTYB-A", "DISC-CTYB-B"):
            self.assertNotIn(forbidden, got)
            self.assertEqual(reasons(rejected)[forbidden], "sai đơn vị")

    def test_level_blocks_executive_salary(self):
        # Chi (level 3) thuộc Công ty B nhưng không thuộc Ban Giám đốc
        for uid in ("an", "binh", "chi"):
            allowed, _ = split_allowed(DOCS, USERS[uid])
            self.assertNotIn("SALARY-BOD-v1", ids(allowed))

    def test_level_check_independent_of_unit(self):
        # Người thuộc đúng đơn vị nhưng level thấp vẫn bị chặn
        low = {"id": "x", "name": "x", "units": ["Appota Group", "Ban Giám đốc"], "level": 1}
        allowed, rejected = split_allowed(DOCS, low)
        self.assertNotIn("SALARY-BOD-v1", ids(allowed))
        self.assertEqual(reasons(rejected)["SALARY-BOD-v1"], "vượt cấp truy cập")

    def test_director_sees_salary(self):
        allowed, _ = split_allowed(DOCS, USERS["gd"])
        self.assertIn("SALARY-BOD-v1", ids(allowed))

    def test_hr_complaint_only_for_hr_level3(self):
        a, _ = split_allowed(DOCS, USERS["an"])
        c, _ = split_allowed(DOCS, USERS["chi"])
        self.assertNotIn("HR-COMPLAINT-v1", ids(a))
        self.assertIn("HR-COMPLAINT-v1", ids(c))

    def test_allowed_and_rejected_partition_all_docs(self):
        for u in USERS.values():
            allowed, rejected = split_allowed(DOCS, u)
            self.assertEqual(len(allowed) + len(rejected), len(DOCS))
            self.assertEqual(ids(allowed) & {d["doc_id"] for d, _ in rejected}, set())


if __name__ == "__main__":
    unittest.main()
