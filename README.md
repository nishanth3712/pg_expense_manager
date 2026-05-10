# 🏠 PG Expense Manager

A Streamlit-based financial dashboard for managing rental property income and expenses, backed by Google Sheets.

⚠️ **SECURITY WARNING**: This app contains sensitive credentials. Never commit `.streamlit/secrets.toml` to GitHub!

## Features

- **Secure Login**: Password-protected access with 3-attempt lockout
- **Monthly Tracking**: Automatic sheet creation for each month
- **Dashboard**: KPIs, income vs expenses chart, transaction history
- **Data Entry**: Easy forms for rent and expense recording
- **Yearly Overview**: Annual summaries with profit trends and expense breakdowns
- **CSV Export**: Download monthly transactions

## Prerequisites

- Python 3.8+
- Google Cloud Service Account with Sheets API access
- Google Spreadsheet

## 🚀 Deployment (GitHub + Streamlit Cloud)

### Step 1: Prepare for GitHub (Public Repo Safe)

1. **Verify `.gitignore` is set up** (already included):
   ```
   .streamlit/secrets.toml
   *.json credentials
   ```

2. **Copy the example secrets file** (don't edit the original):
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

3. **Fill in your actual secrets** in `.streamlit/secrets.toml`:
   - Google Service Account JSON
   - Spreadsheet ID
   - App password

4. **Commit to GitHub** (secrets.toml is automatically excluded):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/pg-expense-manager.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app" → Deploy from your repository
4. **Configure Secrets** (critical step):
   - Go to App Settings → Secrets
   - Copy-paste your entire `.streamlit/secrets.toml` content
   - Save

5. The app deploys automatically without exposing any credentials!

---

## Local Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Sheets API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Sheets API
   - Create a Service Account
   - Download the JSON key file
   - Share your Google Sheet with the service account email

4. Configure secrets:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

   Edit `.streamlit/secrets.toml` with your:
   - Service account credentials (from the JSON key)
   - Spreadsheet ID (from your Google Sheet URL)

5. Run the app:
```bash
streamlit run app.py
```

## Google Sheet Structure

The app automatically creates:
- Monthly sheets (e.g., `May_2026`, `June_2026`) with headers:
  - Date, Category, Description, Type, Mode, Amount
- `Monthly Config` sheet for storing opening balances and profit deductions

## Default Password

**Password**: `jrbloomspg`

You can change this in `.streamlit/secrets.toml`.

## Data Entry Guidelines

### Income/Rent Entry:
- **Mode**: Choose "Cash" or "Bank" for payment method
- **Category**: Automatically set to "Rent"
- **Amount**: Enter the rent amount in INR

### Expense Entry:
- **Categories**: Maintenance, Utilities, Property Tax, Insurance, Mortgage, Misc
- **Mode**: Cash or Bank payment
- **Description**: Brief description of the expense

## Profit Calculation

The app calculates net balance as:
```
Net = (Opening Balance + Total Rent) - Total Expenses - Profit Deducted
```

Where **Profit Deducted** represents withdrawals/owner's draws from the business.

## Troubleshooting

### Connection Errors:
- Verify your service account JSON is correctly formatted in secrets.toml
- Ensure the spreadsheet is shared with the service account email
- Check that the Sheets API is enabled in Google Cloud Console

### Permission Errors:
- Make sure the service account has "Editor" access to the spreadsheet

### Missing Data:
- The dashboard will show zero values until you add transactions
- Configure opening balance and profit deducted using the expander on the dashboard

## Security Notes

- Keep your `secrets.toml` file private and never commit it to version control
- The `.gitignore` should exclude `.streamlit/secrets.toml`
- Use strong passwords for production deployments

## Support

For issues or questions, please check the help section in the app's sidebar.

---

Built with ❤️ using [Streamlit](https://streamlit.io/)
