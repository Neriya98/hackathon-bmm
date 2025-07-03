# Deploying DealSure to Render

This guide provides step-by-step instructions for deploying the DealSure application to Render.

## Prerequisites

- A [Render account](https://render.com)
- Your DealSure codebase pushed to a Git repository (GitHub, GitLab, or Bitbucket)
- Git repository connected to your Render account

## Preparation

Before deploying to Render, you should:

1. **Ensure the Dockerfile is correct**
   
   The Dockerfile has been updated to use:
   - `npm run css:build` instead of `npm run build:css`
   - `gunicorn run:app` instead of `gunicorn app:create_app()`

## Deployment Options

### Option 1: Automatic Deployment with render.yaml (Recommended)

1. **Push the render.yaml to your repository**
   
   The `render.yaml` file in the repository root defines all the services needed for the application.

2. **Create a new Blueprint on Render**
   
   - Go to the Render Dashboard
   - Click "New" > "Blueprint"
   - Select your repository
   - Render will automatically detect the `render.yaml` file and set up all services
   - Review the configuration and click "Apply"

3. **Monitor Deployment**
   
   Render will create and deploy all services defined in the `render.yaml` file:
   - Web service (main application)
   - PostgreSQL database
   - Redis instance
   - Celery worker

### Option 2: Manual Deployment

If you prefer to set up services manually:

1. **Create a PostgreSQL Database**
   
   - In Render Dashboard, click "New" > "PostgreSQL"
   - Name: `dealsure-db`
   - User: `dealsure`
   - Database: `dealsure`
   - Select a plan and region
   - Click "Create Database"
   - Note the internal connection string for later

2. **Create a Redis Instance**
   
   - Click "New" > "Redis"
   - Name: `dealsure-redis`
   - Select a plan and region
   - Click "Create Redis"
   - Note the internal connection string for later

3. **Create Web Service**
   
   - Click "New" > "Web Service"
   - Connect your repository
   - Name: `dealsure`
   - Environment: `Docker`
   - Branch: `main` (or your preferred branch)
   - Root Directory: (leave empty)
   - Click "Create Web Service"

4. **Configure Environment Variables**

   Set the following environment variables:
   - `FLASK_ENV`: `production`
   - `FLASK_DEBUG`: `false`
   - `SECRET_KEY`: (generate a secure random string)
   - `JWT_SECRET_KEY`: (generate a secure random string)
   - `DATABASE_URL`: (use the internal connection string from step 1)
   - `REDIS_URL`: (use the internal connection string from step 2)
   - `CELERY_BROKER_URL`: (same as REDIS_URL)
   - `CELERY_RESULT_BACKEND`: (same as REDIS_URL)
   - `SESSION_COOKIE_SECURE`: `true`
   - `SESSION_COOKIE_HTTPONLY`: `true`
   - `SESSION_COOKIE_SAMESITE`: `Lax`
   - `BITCOIN_NETWORK`: `signet`
   - `BITCOIN_RPC_URL`: `https://blockstream.info/signet/api/`

5. **Create Celery Worker (Optional)**
   
   - Click "New" > "Background Worker"
   - Connect your repository
   - Name: `dealsure-worker`
   - Environment: `Docker`
   - Branch: `main` (or your preferred branch)
   - Root Directory: (leave empty)
   - Build Command: `docker build --target=production .`
   - Start Command: `celery -A app.celery worker --loglevel=info`
   - Add the same environment variables as the web service
   - Click "Create Background Worker"

## Post-Deployment Steps

1. **Initialize the Database**

   Connect to your Render service shell and run:
   ```
   python run.py init-db
   ```

2. **Create Admin User**

   Connect to your Render service shell and run:
   ```
   python run.py create-admin
   ```

3. **Verify Deployment**

   Visit your application URL to ensure everything is working correctly.

## Troubleshooting

- **Build Failures**: Check the build logs for errors. Common issues include missing dependencies or configuration errors.
- **Runtime Errors**: Check the service logs for runtime errors.
- **Database Connection Issues**: Ensure your DATABASE_URL environment variable is correctly set.
- **Redis Connection Issues**: Verify the REDIS_URL environment variable.

## Monitoring and Scaling

- Render provides basic monitoring for all services.
- You can scale your services up or down in the Render dashboard.
- For production workloads, consider upgrading to a paid plan for better performance and reliability.
