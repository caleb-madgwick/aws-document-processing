# AWS setup

Everything here is done by hand in the AWS Console. This project uses its own AWS account,
never the Broski account or the `default` CLI profile.

## Step 1: New account and billing alerts

A separate account is a hard boundary: nothing here can touch Broski, and costs show on their own bill.
Sign up fresh. Don't create it from Broski's AWS Organizations.

1. **Sign up** at <https://portal.aws.amazon.com/billing/signup>.
   - Email: not your Broski one. `you+aws-learning@gmail.com` works.
   - Account name: `ai-learning`. Plan: **Free plan**. Support: **Basic**.
2. **Root MFA:** account name (top right) → **Security credentials** → **Assign MFA device**.
   Never create root access keys.
3. **Billing visibility:** account name → **Account** → *IAM user and role access to Billing
   information* → **Edit** → tick **Activate IAM Access**.
4. **Free Tier alerts:** **Billing and Cost Management** → **Billing preferences** →
   *Alert preferences* → **Edit** → tick **Receive AWS Free Tier alerts**.
5. **Budgets:** **Billing and Cost Management** → **Budgets** → **Create budget** →
   *Use a template*. Create two:
   - **Zero spend budget**, named `ai-learning-zero-spend`
   - **Monthly cost budget** of **$10**, named `ai-learning-monthly`

   Budgets only send emails. They never stop spending.
6. **Account ID:** copy the 12-digit ID (account name, top right) into `.env` as
   `EXPECTED_AWS_ACCOUNT_ID`.

## Step 2: CLI profile `ai-learning`

## Step 3: Least-privilege permissions

## Step 4: S3 bucket

## Step 5: Textract and Bedrock access

## Step 6: Run the pipeline

## Step 7: Check results and costs

## Step 8: Clean up
