import json, tempfile, unittest
from pathlib import Path
import evaluator

class EvaluatorTests(unittest.TestCase):
    def row(self, **extra):
        row={"taskId":"task-01","strategy":"summary","messages":[],"estimatedUnits":1,"operations":[],"callRecords":[],"serviceTokens":None,"quality":None,"status":"completed","modelCalls":1,"answer":{"rawAnswer":"x"}}
        row.update(extra); return row
    def test_known_good_envelope(self):
        self.assertEqual(len(evaluator.validate_envelope({"unit":"estimated-bytes-v1","results":[self.row()]})["results"]),1)
    def test_duplicate_rows_rejected(self):
        r=self.row()
        with self.assertRaises(AssertionError): evaluator.validate_envelope({"unit":"estimated-bytes-v1","results":[r,r]})
    def test_budget_zero_must_not_dispatch(self):
        r=self.row(status="context_budget_exhausted",modelCalls=0,answer=None)
        with self.assertRaises(AssertionError): evaluator.validate_envelope({"unit":"estimated-bytes-v1","results":[dict(r,operations=[{"op":"read"}])]})
    def test_unsupported_claim_shape_is_not_accepted_as_completed(self):
        r=self.row(answer={"rawAnswer":"x","claims":[{"field":"x"}]})
        with self.assertRaises(AssertionError): evaluator.validate_envelope({"unit":"estimated-bytes-v1","results":[r]})

    def test_unknown_must_have_empty_claims(self):
        r=self.row(answer={"rawAnswer":"无足够证据","claims":[{"field":"x","value":"y","source":"doc-01"}],"insufficientEvidence":True})
        with self.assertRaises(AssertionError): evaluator.validate_envelope({"unit":"estimated-bytes-v1","results":[r]})

if __name__=="__main__": unittest.main()
