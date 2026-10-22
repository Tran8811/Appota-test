"""Kiểm thử hồi quy giả lập cho thời hạn, quyền truy cập, mâu thuẫn và trích dẫn."""
import unittest
from datetime import date

from kb.access import split_allowed
from kb.answer import REFUSAL, ask
from kb.loader import load_docs
from kb.retrieve import retrieve

DOCS, _ = load_docs("data")
USER_A = {"user_id": "synthetic-a", "id": "synthetic-a", "units": ["Appota Group", "Công ty B", "Marketing"],
          "level": 1, "corporation": "Appota Group", "company": "Công ty B",
          "department": "Marketing", "position": "Employee"}


def doc(doc_id="P-1", **changes):
    d = {"doc_id": doc_id, "title": "Chính sách OT", "topic": "ot", "scope": "company",
         "owner_unit": "Công ty B", "access_level": 1, "status": "active",
         "effective_date": "2025-01-01", "expiry_date": None,
         "text": "OT mức 20 giờ", "supersedes_document_id": None}
    d.update(changes)
    return d


class TestHardening(unittest.TestCase):
    def test_all_mock_documents_expose_the_complete_metadata_schema(self):
        required = {
            "doc_id", "document_id", "document_title", "document_version", "topic",
            "org_level", "corporation", "company", "department", "team", "scope",
            "access_scope", "owner_unit", "allowed_positions", "access_level", "status",
            "effective_date", "expiry_date", "supersedes_document_id", "source_file",
            "page_number", "section_title",
        }
        self.assertEqual(len(DOCS), 14)
        for document in DOCS:
            self.assertTrue(required.issubset(document), document["doc_id"])
            self.assertIsNotNone(document["expiry_date"], document["doc_id"])

    def test_01_current_and_future_2027(self):
        docs = [doc(), doc("P-2027", effective_date="2027-01-01")]
        allowed, _ = split_allowed(docs, USER_A, date(2026, 10, 22))
        self.assertEqual([d["doc_id"] for d in allowed], ["P-1"])

    def test_02_expired_document(self):
        allowed, _ = split_allowed([doc(expiry_date="2026-10-21")], USER_A, date(2026, 10, 22))
        self.assertEqual(allowed, [])

    def test_mock_active_policy_with_past_expiry_is_rejected(self):
        expired_policy = next(d for d in DOCS if d["doc_id"] == "EXPIRED-DEMO-v1")
        allowed, rejected = split_allowed([expired_policy], USER_A, date(2026, 10, 22))
        self.assertEqual(allowed, [])
        self.assertEqual(rejected[0][1], "đã hết hiệu lực")

    def test_03_missing_effective_date_fails_closed(self):
        allowed, _ = split_allowed([doc(effective_date=None)], USER_A, date(2026, 10, 22))
        self.assertEqual(allowed, [])

    def test_04_company_a_cannot_retrieve_company_b_restricted_doc(self):
        user = dict(USER_A, company="Công ty A", units=["Appota Group", "Công ty A"])
        allowed, _ = split_allowed([doc()], user)
        self.assertEqual(allowed, [])

    def test_05_group_and_company_sources_remain_ranked(self):
        allowed, _ = split_allowed(DOCS, USER_A)
        result = retrieve("Quy định OT của tôi?", allowed)
        self.assertTrue(any("OT-GROUP-v1" in [d["doc_id"] for d in t["primary"] + t["lower_priority"]]
                            for t in result["topics"]))

    def test_06_position_allowlist_is_enforced(self):
        allowed, _ = split_allowed([doc(allowed_positions=["manager"])], USER_A)
        self.assertEqual(allowed, [])

    def test_07_declared_replacement_wins(self):
        a = doc("POLICY-v1")
        b = doc("POLICY-v2", supersedes_document_id="POLICY-v1", text="OT mức 25 giờ")
        result = retrieve("Chính sách OT hiện hành?", [a, b])
        self.assertEqual([d["doc_id"] for t in result["topics"] for d in t["primary"]], ["POLICY-v2"])

    def test_08_unresolved_same_rank_is_conflict(self):
        result = retrieve("Chính sách OT hiện hành?", [doc("POLICY-A"), doc("POLICY-B", text="OT mức 30 giờ")])
        self.assertEqual(result["status"], "conflict")

    def test_09_unsupported_question_is_refused(self):
        result = ask("Chính sách bảo hiểm sức khỏe?", USER_A, DOCS, lambda *_: self.fail("LLM called"))
        self.assertEqual(result["answer"], REFUSAL)

    def test_10_citation_page_is_metadata_only_and_unknown_is_explicit(self):
        d = doc(page_number=None, section_title=None)
        result = ask("Chính sách OT?", USER_A, [d], lambda *_: "Kết luận [P-1]")
        self.assertIsNone(result["sources"][0]["page_number"])
        self.assertIn("trang: chưa xác định", result["prompt"])

    def test_markdown_citation_uses_section_and_excerpt_without_fake_page(self):
        result = ask("Quy định OT của tôi?", USER_A, DOCS, lambda *_: "OT tối đa 30 giờ [OT-MKT-v1]")
        source = next(s for s in result["sources"] if s["doc_id"] == "OT-MKT-v1")
        self.assertTrue(source["section_title"])
        self.assertIn("OT tối đa 30 giờ", source["excerpt"])
        self.assertEqual(source["page_reference"], "không áp dụng (Markdown)")

    def test_pdf_citation_uses_extracted_page_number(self):
        result = ask("Thời hạn thanh toán chi phí công tác là bao lâu?", USER_A, DOCS,
                     lambda *_: "Tài chính thanh toán trong 7 ngày làm việc [TRAVEL-EXPENSE-PDF-v1]")
        source = next(s for s in result["sources"] if s["doc_id"] == "TRAVEL-EXPENSE-PDF-v1")
        self.assertEqual(source["page_number"], 1)
        self.assertEqual(source["page_reference"], "1")
        self.assertEqual(source["source_file"], "chi_phi_cong_tac_demo.pdf")
        self.assertIn("7 ngày làm việc", source["excerpt"])

    def test_11_retrieved_document_does_not_automatically_validate_claim(self):
        result = ask("Chính sách OT?", USER_A, [doc()], lambda *_: "Mức là 999 giờ [P-1]")
        self.assertTrue(any("không đối chiếu được" in warning for warning in result["warnings"]))

    def test_13_valid_bare_document_ids_and_grounded_numbers_do_not_warn(self):
        answer = ("Bạn được hưởng 14 ngày phép theo Quy định nghỉ phép Công ty B, LEAVE-CTYB-v1. "
                  "Mức chung là 12 ngày theo Quy định nghỉ phép Tập đoàn, LEAVE-GROUP-v2.")
        result = ask("Quy định nghỉ phép của tôi như thế nào?", USER_A, DOCS, lambda *_: answer)
        self.assertEqual(result["warnings"], [])

    def test_12_historical_query_date_selects_historically_effective_record(self):
        d = doc(effective_date="2024-01-01", expiry_date="2025-12-31")
        allowed, _ = split_allowed([d], USER_A, date(2025, 6, 1))
        self.assertEqual([x["doc_id"] for x in allowed], ["P-1"])

    def test_future_relevant_document_is_reported_but_not_used(self):
        current = doc(text="OT tối đa 20 giờ mỗi tháng.")
        future = doc("P-2027", effective_date="2027-01-01", text="OT tối đa 25 giờ mỗi tháng.")
        result = ask("Chính sách OT hiện hành?", USER_A, [current, future],
                     lambda *_: "Theo tài liệu hiện hành, OT tối đa 20 giờ [P-1].",
                     query_date=date(2026, 10, 22))
        self.assertIn("P-1", {s["doc_id"] for s in result["sources"]})
        self.assertNotIn("P-2027", {s["doc_id"] for s in result["sources"]})
        self.assertEqual([d["doc_id"] for d in result["future_documents"]], ["P-2027"])
        self.assertIn("2027-01-01", result["answer"])

    def test_2027_leave_policy_is_announced_now_and_selected_for_2027(self):
        from tests.test_access import USERS
        current = ask("Quy định nghỉ phép của tôi?", USERS["binh"], DOCS,
                      lambda *_: "Theo tài liệu hiện hành, 12 ngày phép [LEAVE-GROUP-v2].",
                      query_date=date(2026, 10, 22))
        self.assertEqual([d["doc_id"] for d in current["future_documents"]], ["LEAVE-GROUP-v3-2027"])
        self.assertNotIn("LEAVE-GROUP-v3-2027", {s["doc_id"] for s in current["sources"]})
        future = ask("Quy định nghỉ phép của tôi trong năm 2027?", USERS["binh"], DOCS,
                     lambda *_: "Theo quy định năm 2027, có 13 ngày phép [LEAVE-GROUP-v3-2027].")
        self.assertEqual([s["doc_id"] for s in future["sources"] if s["role"] == "áp dụng"],
                         ["LEAVE-GROUP-v3-2027"])

    def test_latest_effective_same_scope_policy_wins(self):
        older = doc("POLICY-OLD", effective_date="2025-01-01", text="OT tối đa 20 giờ.")
        newer = doc("POLICY-NEW", effective_date="2026-01-01", text="OT tối đa 25 giờ.")
        result = retrieve("Chính sách OT hiện hành?", [older, newer])
        selected = [d["doc_id"] for t in result["topics"] for d in t["primary"]]
        self.assertEqual(selected, ["POLICY-NEW"])

    def test_latest_expiry_breaks_same_effective_date_tie(self):
        shorter = doc("POLICY-SHORT", effective_date="2025-01-01", expiry_date="2026-12-31")
        longer = doc("POLICY-LONG", effective_date="2025-01-01", expiry_date="2027-12-31")
        result = retrieve("Chính sách OT hiện hành?", [shorter, longer])
        selected = [d["doc_id"] for t in result["topics"] for d in t["primary"]]
        self.assertEqual(selected, ["POLICY-LONG"])

    def test_structured_corporation_mismatch_denies_even_if_company_name_matches(self):
        restricted = doc(corporation="Other Group", company="Công ty B", owner_unit="Công ty B")
        allowed, _ = split_allowed([restricted], USER_A)
        self.assertEqual(allowed, [])


if __name__ == "__main__":
    unittest.main()
