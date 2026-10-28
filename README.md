# AWS Document Processing

Extracting and validating supplier invoice data with Amazon S3, Amazon Textract and Claude on Amazon Bedrock. All invoices are fictional.

![Architecture diagram](docs/architecture.svg)

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

AWS setup is done by hand in the Console: see [docs/aws-setup.md](docs/aws-setup.md).

## Tests

```bash
pytest
```

The tests don't call AWS.
