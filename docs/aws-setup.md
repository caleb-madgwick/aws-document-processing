# AWS setup

Everything here is done by hand in the AWS Console. This project uses its own personal AWS account,
never another AWS account or the `default` CLI profile.

The account was made with AWS's newer sign-up, which organises it into **projects**. Each project is
its own AWS account in one Region, with its own account ID and spend limit. All projects are owned by
your **AWS Builder ID** (your personal AWS login); there is no root user. You manage projects,
billing and limits at <https://settings.aws.com>.

This pipeline gets a project of its own, so cleaning up at the end means closing that one project.

## Step 1: Project, spend limit and budget

1. **MFA on your Builder ID.** The Builder ID owns every project, so it's the login to protect:
   <https://profile.aws.amazon.com> → **Security** → register an MFA device.
2. **Paid plan.** Amazon Textract is only available on the Paid plan. The upgrade covers all your
   projects and keeps your credits. Don't choose **Activate advanced features**: it can't be undone
   and it removes spend limits.
3. **Create the project.** **settings.aws.com** → **Project** → **Create project** → name it
   `InvoicePipeline` → **Create**. Names can only use letters, numbers and periods.
4. **Spend limit.** This is a hard cap. If the project's costs reach it, AWS pauses the project and
   stops its resources.
   - **settings.aws.com** → **Billing** → *Cost by project* → **Set limit** on `InvoicePipeline`.
   - Choose a custom limit of **$20**, the lowest AWS allows, then **Set spend limit**.
   - Tick **Stop new resource launches** and **Pause top cost drivers**, then
     **Save early cost controls**.

   The limit applies to pre-tax charges, and AWS says it excludes credits. A paused project keeps its
   data, but AWS deletes it if you take no action within 90 days.
5. **Budget.** A budget only sends emails; it never stops anything. It warns you well before the
   spend limit does. Open the `InvoicePipeline` project's console first, so the budget belongs to it.
   - **Billing and Cost Management** → **Budgets** → **Create budget** → *Use a template*.
   - Choose **Monthly cost budget** of **$5**, named `invoice-pipeline-monthly`, using your email.
6. **Region and account ID.** **settings.aws.com** → **Project** → `InvoicePipeline` →
   *Overview* → **Additional info**. Copy both into `.env`:
   ```
   EXPECTED_AWS_ACCOUNT_ID=<12-digit account ID>
   AWS_REGION=<the Region shown, e.g. ap-southeast-2>
   ```
   The code refuses to run unless the credentials it's given belong to this account ID.

## Step 2: CLI login

The Python code needs AWS credentials. `aws login` gets temporary ones through your browser
sign-in, so no access keys are saved on disk or committed anywhere. They last 12 hours and renew
automatically for up to 90 days. Each project needs its own profile.

1. Check the CLI is **2.32.0 or newer** (needed for `aws login`):
   ```bash
   aws --version
   ```
2. Sign in to a new profile named `invoice-pipeline-login`. This adds one new section to
   `~/.aws/config` and leaves your other profiles alone.
   ```bash
   aws login --profile invoice-pipeline-login
   ```
   - When asked for a Region, enter the Region from Step 1.
   - In the browser, choose the `InvoicePipeline` project.
3. Check the profile points at the right account:
   ```bash
   aws sts get-caller-identity --profile invoice-pipeline-login
   ```
   `Account` must equal `EXPECTED_AWS_ACCOUNT_ID`. If it doesn't, stop and run
   `aws logout --profile invoice-pipeline-login`.

This login can do anything in the project, so the pipeline won't use it directly. Step 5 creates a
role that can only reach this project's bucket, Textract and Bedrock, and the `invoice-pipeline`
profile uses that role.

To sign out: `aws logout --profile invoice-pipeline-login`.

## Step 3: S3 bucket

Amazon S3 stores files ("objects") in a container called a **bucket**. Textract reads each invoice
PDF from here, so the bucket must be in the same Region as the Textract calls.

1. Open the `InvoicePipeline` project's console and check the Region (top right) is your project's.
2. **S3** → **Create bucket**:
   - **Bucket type:** General purpose.
   - **Bucket name:** `invoice-pipeline-<something unique>`, e.g. `invoice-pipeline-cm-4821`.
     Names are global across all of AWS, so a plain `invoice-pipeline` is taken.
   - **Object Ownership:** ACLs disabled (the default).
   - **Block all public access:** leave it ticked. Nothing here should ever be public.
   - **Bucket Versioning:** Disable, so deleting a file really deletes it.
   - **Tags:** key `project`, value `invoice-pipeline`.
   - **Default encryption:** leave as SSE-S3 (Amazon S3 managed keys).
   - **Create bucket**.
3. Put the name in `.env` as `S3_BUCKET`, then check the CLI can see it. No output and no error means
   it worked, because the bucket is empty:
   ```bash
   aws s3 ls s3://<your-bucket-name> --profile invoice-pipeline-login
   ```

**Cost:** a few small PDFs cost a fraction of a cent a month to store, plus a fraction of a cent per
thousand uploads.

## Step 4: Bedrock model access

Amazon Bedrock runs AI models from several companies behind one AWS API. This project uses
**Claude Haiku 5.5**: cheap, fast, and plenty for reading seven fields off an invoice.

Claude is sold through AWS Marketplace, so your account needs a one-off agreement with Anthropic
before the first call. Sending one message in the playground sets that up.

1. In the `InvoicePipeline` console (Region `ap-southeast-2`): **Amazon Bedrock** → **Playground**
   (or **Chat / Text playground**) → **Select model** → **Anthropic** → **Claude Haiku 5.5**.
2. Fill in Anthropic's use-case form if it appears. Describe the project honestly, for example
   "Personal learning project extracting fields from fictional invoices."
3. Accept the offer terms if asked, then send `Say hello`. A reply means access works.

Charges appear on your AWS bill under Anthropic, not Amazon Bedrock.

**Cost:** about $0.10 per million input tokens and $0.50 per million output tokens. One invoice is
roughly 1,500 tokens in and 200 out, so well under a tenth of a cent.

## Step 5: Least-privilege role

## Step 6: Run the pipeline

## Step 7: Check results and costs

## Step 8: Clean up

Close the project: **settings.aws.com** → `InvoicePipeline` → **Close project**. You can reopen it
within 90 days; after that AWS deletes everything in it.
