-- Run this in DBeaver to add auth support.
-- The products table already has data, so we handle that with a default.

-- 1. Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. Add user_id column to products (allow NULL first, then backfill)
ALTER TABLE products ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- 3. If you have existing products with no user, you can either:
--    a) Delete them: DELETE FROM products WHERE user_id IS NULL;
--    b) Or create a default user first and assign them:
--       INSERT INTO users (email, hashed_password) VALUES ('admin@pricewatch.local', 'placeholder');
--       UPDATE products SET user_id = (SELECT id FROM users LIMIT 1) WHERE user_id IS NULL;

-- 4. Once all rows have a user_id, add the NOT NULL constraint:
-- ALTER TABLE products ALTER COLUMN user_id SET NOT NULL;

-- 5. Add index
CREATE INDEX IF NOT EXISTS ix_products_user_id ON products(user_id);
