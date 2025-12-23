# Meal Planner Setup Guide

## Step 1: Set Up Supabase Database

1. **Log in to Supabase**
   - Go to https://supabase.com and log in to your account
   - Navigate to your project: https://dxfcfcyvlkxdhikzzsqs.supabase.co

2. **Run the SQL Schema**
   - In your Supabase dashboard, click on the **SQL Editor** in the left sidebar
   - Click **"New Query"**
   - Copy the entire contents of `supabase-schema.sql` file
   - Paste it into the SQL editor
   - Click **"Run"** or press `Ctrl+Enter`
   - You should see a success message

3. **Verify Table Creation**
   - Click on **"Table Editor"** in the left sidebar
   - You should see a new table called `meals`
   - The table will be empty - that's normal! The app will auto-seed it on first load.

## Step 2: Enable GitHub Pages

1. **Go to Repository Settings**
   - Visit: https://github.com/smitcal/Christopher-Smith-Finance-professional/settings/pages

2. **Configure Pages Source**
   - Under "Build and deployment"
   - **Source**: Select "GitHub Actions"
   - Click **Save**

3. **Wait for Deployment**
   - Go to the **Actions** tab in your repository
   - You should see a workflow called "Deploy Meal Planner to GitHub Pages" running
   - Wait for it to complete (usually takes 1-2 minutes)
   - Once complete, you'll see a green checkmark

## Step 3: Access Your Meal Planner

Your meal planner will be live at:

**https://smitcal.github.io/Christopher-Smith-Finance-professional/meal-planner/**

## Troubleshooting

### If the page shows a 404 error:
1. Make sure GitHub Pages is enabled in repository settings
2. Check that the workflow completed successfully in the Actions tab
3. Wait a few minutes - Pages can take 5-10 minutes to fully deploy the first time

### If you see a database error:
1. Make sure you ran the SQL schema in Supabase
2. Check that the credentials in `index.html` match your Supabase project
3. Verify your Supabase project is active

### If meals don't load:
1. Open browser developer console (F12)
2. Check for any error messages
3. Verify your Supabase project URL is accessible

## What Happens on First Load

When you first open the app:
1. It checks if the `meals` table is empty
2. If empty, it automatically seeds with 35 meals from your master list
3. All meals start in the Library (not on the Dashboard)
4. You can then use Quick Add or add meals from the Library

## Next Steps

Once everything is set up:
- Open the app on your phone (it's mobile-optimized!)
- Try adding a meal with Quick Add
- Move meals between Library and Dashboard
- Mark meals as eaten with "We Ate This"

Enjoy your meal planning! 🍽️
