import copy
import json
import unittest
from datetime import date

from kb.access import split_allowed
from kb.answer import CLARIFICATION, ask
from kb.loader import load_docs
from kb.retrieve import retrieve

USERS = {u["id"]: u for u in json.load(open("users.json", encoding="utf-8"))}
DOCS, _ = load_docs("data")


class FakeLLM:
    def __init__(self):
        self.calls = []

    def __call__(self, system, prompt):
        self.calls.append((system, prompt))
        return "Câu trả lời [OT-MKT-v1] [OT-GROUP-v1]"


class TestMission3Improvements(unittest.TestCase):
    def test_change_request_cr01_unknown_effective_date_fails_closed(self):
        """CR-M3-01 kiểm tra ngày thiếu hoặc sai được xem là chưa xác định, không tự suy đoán."""
        doc = copy.deepcopy(next(d for d in DOCS if d["doc_id"] == "OT-MKT-v1"))
        doc["effective_date"] = None

        allowed, rejected = split_allowed([doc], USERS["an"], as_of=date(2026, 10, 22))

        self.assertEqual(allowed, [])
        self.assertEqual(rejected[0][1], "chưa xác định ngày hiệu lực")

    def test_edge_expiry_date_is_valid_through_end_of_calendar_day(self):
        """Ngày hết hạn được tính trọn ngày; tài liệu hết hiệu lực từ ngày hôm sau."""
        doc = copy.deepcopy(next(d for d in DOCS if d["doc_id"] == "OT-MKT-v1"))
        doc["expiry_date"] = "2026-10-22"

        valid_on_expiry, _ = split_allowed([doc], USERS["an"], as_of=date(2026, 10, 22))
        expired_next_day, _ = split_allowed([doc], USERS["an"], as_of=date(2026, 10, 23))

        self.assertEqual([d["doc_id"] for d in valid_on_expiry], ["OT-MKT-v1"])
        self.assertEqual(expired_next_day, [])

    def test_regression_mission2_user_scope_still_hides_company_b_policy(self):
        """Hồi quy quyền cũ: người dùng Công ty C không tìm thấy quy định nghỉ phép Công ty B."""
        allowed, _ = split_allowed(DOCS, USERS["binh"])

        result = retrieve("Quy định nghỉ phép của tôi như thế nào?", allowed)
        selected = {d["doc_id"] for topic in result["topics"]
                    for d in topic["primary"] + topic["lower_priority"]}

        self.assertIn("LEAVE-GROUP-v2", selected)
        self.assertNotIn("LEAVE-CTYB-v1", selected)

    def test_future_effective_document_is_excluded(self):
        future_doc = copy.deepcopy(next(d for d in DOCS if d["doc_id"] == "OT-MKT-v1"))
        future_doc["effective_date"] = "2026-11-01"

        allowed, rejected = split_allowed(
            [future_doc], USERS["an"], as_of=date(2026, 10, 22)
        )

        self.assertEqual(allowed, [])
        self.assertEqual(rejected, [(future_doc, "chưa đến ngày hiệu lực (2026-11-01)")])

    def test_partial_override_keeps_general_and_specific_sources(self):
        llm = FakeLLM()
        result = ask("OT được trả bao nhiêu tiền?", USERS["an"], DOCS, llm)
        prompt = llm.calls[0][1]

        self.assertIn("OT-MKT-v1", prompt)
        self.assertIn("OT-GROUP-v1", prompt)
        self.assertIn("150% lương giờ", prompt)
        self.assertIn("quy đổi thành ngày nghỉ bù", prompt)

    def test_ambiguous_penalty_question_requests_clarification(self):
        llm = FakeLLM()

        result = ask("Phạt bao nhiêu?", USERS["an"], DOCS, llm)

        self.assertEqual(result["retrieval"]["status"], "clarify")
        self.assertEqual(result["answer"], CLARIFICATION)
        self.assertFalse(result["llm_called"])
        self.assertEqual(llm.calls, [])

    def test_source_details_are_verifiable_and_authorized(self):
        llm = FakeLLM()
        result = ask("Quy định OT của tôi?", USERS["an"], DOCS, llm)

        sources = {source["doc_id"]: source for source in result["sources"]}
        self.assertEqual(set(sources), {"OT-MKT-v1", "OT-GROUP-v1"})
        self.assertIn("30 giờ", sources["OT-MKT-v1"]["text"])
        self.assertIn("150%", sources["OT-GROUP-v1"]["text"])

    def test_same_scope_older_active_version_is_not_a_source(self):
        old_doc = copy.deepcopy(next(d for d in DOCS if d["doc_id"] == "LEAVE-GROUP-v2"))
        old_doc.update(doc_id="LEAVE-GROUP-v1-active", document_id="LEAVE-GROUP-v1-active",
                       document_version="v1", version="v1", effective_date="2025-01-01")
        allowed, _ = split_allowed([old_doc, *DOCS], USERS["binh"])

        result = retrieve("Quy định nghỉ phép của tôi như thế nào?", allowed)
        selected = [
            d["doc_id"]
            for topic in result["topics"]
            for d in topic["primary"] + topic["lower_priority"]
        ]

        self.assertIn("LEAVE-GROUP-v2", selected)
        self.assertNotIn("LEAVE-GROUP-v1-active", selected)

    def test_regression_same_question_still_obeys_user_scope(self):
        an_allowed, _ = split_allowed(DOCS, USERS["an"])
        binh_allowed, _ = split_allowed(DOCS, USERS["binh"])

        an_result = retrieve("Quy định nghỉ phép của tôi như thế nào?", an_allowed)
        binh_result = retrieve("Quy định nghỉ phép của tôi như thế nào?", binh_allowed)
        an_ids = {d["doc_id"] for t in an_result["topics"] for d in t["primary"]}
        binh_ids = {d["doc_id"] for t in binh_result["topics"] for d in t["primary"]}

        self.assertIn("LEAVE-CTYB-v1", an_ids)
        self.assertEqual(binh_ids, {"LEAVE-GROUP-v2"})
        self.assertNotIn("LEAVE-CTYB-v1", binh_ids)


if __name__ == "__main__":
    unittest.main()
