import json
import unittest

from kb.access import split_allowed
from kb.loader import load_docs
from kb.retrieve import retrieve

USERS = {u["id"]: u for u in json.load(open("users.json", encoding="utf-8"))}
DOCS, _ = load_docs("data")


def run(uid, question):
    allowed, _ = split_allowed(DOCS, USERS[uid])
    return retrieve(question, allowed)


def primary_ids(r):
    return [d["doc_id"] for t in r["topics"] for d in t["primary"]]


def lower_ids(r):
    return [d["doc_id"] for t in r["topics"] for d in t["lower_priority"]]


class TestSameQuestionDifferentUsers(unittest.TestCase):
    Q = "Quy định nghỉ phép của tôi như thế nào?"

    def test_an_gets_company_b(self):
        r = run("an", self.Q)
        self.assertEqual(primary_ids(r), ["LEAVE-CTYB-v1"])
        self.assertEqual(lower_ids(r), ["LEAVE-GROUP-v2"])  # để nêu sự khác biệt

    def test_binh_gets_group(self):
        r = run("binh", self.Q)
        self.assertEqual(primary_ids(r), ["LEAVE-GROUP-v2"])
        self.assertEqual(lower_ids(r), [])

    def test_archived_version_never_used(self):
        for uid in USERS:
            r = run(uid, self.Q)
            self.assertNotIn("LEAVE-GROUP-v1", primary_ids(r) + lower_ids(r))

    def test_ot_marketing_overrides_group_only_for_marketing(self):
        self.assertEqual(primary_ids(run("an", "Quy định OT của tôi?")), ["OT-MKT-v1"])
        self.assertEqual(primary_ids(run("binh", "Quy định OT của tôi?")), ["OT-GROUP-v1"])


class TestRefusalAndPermission(unittest.TestCase):
    def test_vietnamese_overtime_synonym_retrieves_ot_documents(self):
        result = run("an", "Quy định tăng ca thế nào?")
        self.assertIn("OT-MKT-v1", primary_ids(result))

    def test_salary_not_retrievable_by_low_level(self):
        for uid in ("an", "binh", "chi"):
            r = run(uid, "Lương của Tổng Giám đốc là bao nhiêu?")
            self.assertNotIn("SALARY-BOD-v1", primary_ids(r) + lower_ids(r))
            self.assertEqual(r["status"], "no_answer")

    def test_salary_retrievable_by_director(self):
        r = run("gd", "Lương của Tổng Giám đốc là bao nhiêu?")
        self.assertEqual(primary_ids(r), ["SALARY-BOD-v1"])

    def test_unknown_topic_is_refused(self):
        for uid in USERS:
            self.assertEqual(run(uid, "Chính sách bảo hiểm sức khỏe?")["status"], "no_answer")

    def test_empty_keywords_refused(self):
        self.assertEqual(run("an", "Quy định thế nào?")["status"], "no_answer")


class TestConflict(unittest.TestCase):
    def test_same_scope_same_date_is_conflict(self):
        r = run("an", "Đi muộn bị phạt bao nhiêu?")
        self.assertEqual(r["status"], "conflict")
        self.assertEqual(sorted(primary_ids(r)), ["DISC-CTYB-A", "DISC-CTYB-B"])

    def test_other_company_does_not_see_conflict_docs(self):
        self.assertEqual(run("binh", "Đi muộn bị phạt bao nhiêu?")["status"], "no_answer")


if __name__ == "__main__":
    unittest.main()
