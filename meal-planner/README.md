# 🍽️ Serverless Meal Planner

A simple, mobile-friendly meal planning app built with Supabase and deployed on GitHub Pages.

## Features

- **Dashboard Tab**: View meals currently in your "To Eat" queue
- **Library Tab**: Browse all available meals and add them to your dashboard
- **Quick Add**: Instantly add new meals that go directly to both Library and Dashboard
- **We Ate This**: Remove meals from dashboard while keeping them in the library
- **Auto-Seeding**: Automatically populates the database with a master meal list on first run

## Tech Stack

- Single HTML file
- Tailwind CSS (CDN)
- Supabase JS Client (CDN)
- No build process required!

## Setup Instructions

### 1. Set Up Supabase Database

1. Log in to your Supabase dashboard at https://supabase.com
2. Navigate to the SQL Editor
3. Copy and paste the contents of `supabase-schema.sql`
4. Run the SQL to create the `meals` table

### 2. Deploy to GitHub Pages

The app is already configured with your Supabase credentials and ready to use!

Simply enable GitHub Pages:
1. Go to your repository Settings
2. Navigate to Pages
3. Select the branch and `/meal-planner` folder
4. Save and wait for deployment

### 3. Access Your App

Once deployed, your meal planner will be available at:
`https://[your-username].github.io/[repository-name]/meal-planner/`

## Usage

### Adding Meals
- Use the **Quick Add** input at the top to add a new meal
- This adds the meal to both your Library and Dashboard instantly

### Managing Dashboard
- Click **"We Ate This"** on any dashboard card to remove it from your queue
- The meal stays in your Library for future use
- Go to the Library tab to add meals back to your dashboard

### Library
- View all available meals
- Click **"Add to Dashboard"** to add a meal to your eating queue

## Database Schema

The app uses a single `meals` table with the following structure:

```sql
CREATE TABLE meals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    in_dashboard BOOLEAN DEFAULT false,
    dashboard_added_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Auto-Seeding

On first load, if the database is empty, the app automatically populates it with 35 delicious meal options including:
- Chicken Pot Pie
- Lamb Casserole
- Beef Stir Fry
- And many more!

## Mobile Friendly

The app is fully responsive and optimized for mobile devices, making it easy to plan meals on the go.

## Live App

Access your meal planner at: https://smitcal.github.io/Christopher-Smith-Finance-professional/meal-planner/

## License

Free to use and modify for personal use.
