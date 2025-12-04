-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. User API Keys
create table if not exists public.user_api_keys (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    provider text not null,
    api_key text,
    model text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(user_id, provider)
);

-- 2. YouTube Tokens (Stores the JSON content of token.json)
create table if not exists public.youtube_tokens (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    token_data jsonb not null,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(user_id)
);

-- 3. Automation Settings
create table if not exists public.automation_settings (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    active boolean default false,
    frequency integer default 24, -- Hours
    last_run timestamp with time zone,
    next_run timestamp with time zone,
    updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
    unique(user_id)
);

-- 4. Optimization History
create table if not exists public.optimization_history (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    video_id text not null,
    video_title text,
    action_taken text, -- 'optimized', 'uploaded', etc.
    details jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 5. Pending Reviews
create table if not exists public.pending_reviews (
    id uuid default uuid_generate_v4() primary key,
    user_id uuid references auth.users(id) on delete cascade not null,
    video_id text not null,
    original_data jsonb,
    suggested_data jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.user_api_keys enable row level security;
alter table public.youtube_tokens enable row level security;
alter table public.automation_settings enable row level security;
alter table public.optimization_history enable row level security;
alter table public.pending_reviews enable row level security;

-- Create Policies (Users can only see/edit their own data)

-- user_api_keys
create policy "Users can view their own keys" on public.user_api_keys
    for select using (auth.uid() = user_id);
create policy "Users can insert their own keys" on public.user_api_keys
    for insert with check (auth.uid() = user_id);
create policy "Users can update their own keys" on public.user_api_keys
    for update using (auth.uid() = user_id);
create policy "Users can delete their own keys" on public.user_api_keys
    for delete using (auth.uid() = user_id);

-- youtube_tokens
create policy "Users can view their own tokens" on public.youtube_tokens
    for select using (auth.uid() = user_id);
create policy "Users can insert their own tokens" on public.youtube_tokens
    for insert with check (auth.uid() = user_id);
create policy "Users can update their own tokens" on public.youtube_tokens
    for update using (auth.uid() = user_id);

-- automation_settings
create policy "Users can view their own settings" on public.automation_settings
    for select using (auth.uid() = user_id);
create policy "Users can insert their own settings" on public.automation_settings
    for insert with check (auth.uid() = user_id);
create policy "Users can update their own settings" on public.automation_settings
    for update using (auth.uid() = user_id);

-- optimization_history
create policy "Users can view their own history" on public.optimization_history
    for select using (auth.uid() = user_id);
create policy "Users can insert their own history" on public.optimization_history
    for insert with check (auth.uid() = user_id);

-- pending_reviews
create policy "Users can view their own reviews" on public.pending_reviews
    for select using (auth.uid() = user_id);
create policy "Users can insert their own reviews" on public.pending_reviews
    for insert with check (auth.uid() = user_id);
create policy "Users can update their own reviews" on public.pending_reviews
    for update using (auth.uid() = user_id);
create policy "Users can delete their own reviews" on public.pending_reviews
    for delete using (auth.uid() = user_id);
