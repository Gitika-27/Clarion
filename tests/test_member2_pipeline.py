from ai.ingestion.pdf_parser import parse_pdf
from ai.ingestion.extraction.extractor import extract_fields
from ai.ingestion.identity_resolver import propose_match


def test_member2_pipeline():

    # Step 1: Parse PDF
    chunks = parse_pdf(
        "data/samples/Test1.pdf",
        "Test1"
    )

    print("PDF chunks:", len(chunks))

    assert len(chunks) > 0

    # Step 2: Extract fields
    fields = extract_fields(chunks)

    print("Extracted fields:", len(fields))

    assert len(fields) > 0

    # Step 3: Identity resolution
    identity_result = propose_match(
        "Test1",
        "Hydraulic Pump HP500",
        "Test2",
        "HP500 Hydraulic Pump"
    )

    print("Identity result:", identity_result)

    print("MEMBER 2 PIPELINE TEST PASSED")


if __name__ == "__main__":
    test_member2_pipeline()