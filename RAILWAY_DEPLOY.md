# Railway deployment

1. Push this folder/repository to GitHub.
2. Create a Railway service from the repository.
3. Add these Railway Variables:
   - API_ID
   - API_HASH
   - BOT_TOKEN
4. Deploy using the included Dockerfile.
5. Check the deployment logs. The application will fail fast with a clear message if a required variable is missing.

Secrets are intentionally not included in this archive.

Note: this package only prepares the application's deployment configuration. It does not add or modify DRM circumvention/decryption functionality.
