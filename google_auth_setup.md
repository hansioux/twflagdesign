# How to Get Google OAuth Credentials

To enable "Login with Google", you need to register this application in the Google Cloud Console.

## Step 1: Create a Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown (top left) and select **New Project**.
3. Name it `twflagdesign-dev` and click **Create**.

## Step 2: Configure OAuth Consent Screen
1. In the left sidebar, navigate to **APIs & Services** > **OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill in the required fields:
   - **App Name**: TW Flag Design
   - **User Support Email**: Select your email.
   - **Developer Contact Information**: Enter your email.
4. Click **Save and Continue** through the "Scopes" and "Test Users" sections (you can leave them default for now).
5. **Crucial**: Go back to the Dashboard and click **Publish App** (or add your specific email to "Test Users" if you don't want to publish yet).

## Step 3: Create Credentials
1. In the left sidebar, go to **APIs & Services** > **Credentials**.
2. Click **+ CREATE CREDENTIALS** (top) > **OAuth client ID**.
3. **Application Type**: Select **Web application**.
4. **Name**: `Flask App Local`.
5. **Authorized Redirect URIs**:
   - Click **ADD URI**.
   - Enter: `http://127.0.0.1:8000/auth/authorize`
   - *Note*: If you use port 5000, use `http://127.0.0.1:5000/auth/authorize`.
6. Click **Create**.

## Step 4: Get Your Keys
1. You will see a popup with **Your Client ID** and **Your Client Secret**.
2. Copy these strings.

## Step 5: Configure Application
Open `start_app.sh` and fill in the values:

```bash
export GOOGLE_CLIENT_ID='paste-your-client-id-here'
export GOOGLE_CLIENT_SECRET='paste-your-client-secret-here'
```
