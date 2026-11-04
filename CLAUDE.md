# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AI-Powered E-commerce Application with an Intelligent Shopping Assistant. Full-stack: **Django REST Framework** backend + **React** frontend (frontend not yet started), **SQLite** dev database, local **Ollama** LLM for the planned shopping assistant. Built incrementally in approved phases (see "Development phases" below).

## Environment & commands

All backend work happens in `backend/`. The virtualenv lives at `backend/venv/` and was bootstrapped with `get-pip.py` because this machine lacks the `python3.12-venv` apt package — it is a normal, working venv.

```bash
cd backend
source venv/bin/activate            # or prefix commands with venv/bin/

python manage.py runserver 8001     # see port note below
python manage.py migrate            # apply migrations
python manage.py makemigrations <app>
python manage.py seed_products      # load sample categories/products (re-runnable)
python manage.py createsuperuser    # prompts for EMAIL (no username) + password
python manage.py check
python manage.py test               # test runner — but NO unit tests exist yet
```

**Port note:** `:8000` is occupied by another process on this machine, so run the dev/test server on **`:8001`**. The project owner also runs their own instance on `0.0.0.0:8099 --noreload` (note `--noreload` means it will NOT pick up new code until restarted). When starting a test server, bind `127.0.0.1:8001` and stop only that process (`pkill -f "runserver 127.0.0.1:8001"`) so the owner's `:8099` server is left alone.

**Testing is done manually via `curl`, not a test suite.** The `tests.py` files are empty boilerplate. Verify changes by starting the server and exercising endpoints with `curl` (log in to get a JWT access token, pass it as `Authorization: Bearer <token>`).

## Configuration

Secrets/config are read from `backend/.env` via `python-decouple` — never hardcode them in `settings.py`. `backend/.env.example` is the committed template. Key vars: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `JWT_ACCESS_MINUTES`, `JWT_REFRESH_DAYS`, `OLLAMA_BASE_URL`, `OLLAMA_MODEL`. `.env`, `db.sqlite3`, `venv/`, `media/`, and `backend/backups/` are gitignored.

## Architecture

Django project is **`config`** (`backend/config/`). Apps are enabled incrementally in `settings.py` → `LOCAL_APPS` as each phase lands. Each app owns a `urls.py` that `config/urls.py` includes under an `/api/...` prefix.

**URL map:** `/api/health/`, `/api/auth/` (accounts), `/api/` (products router: `/products/`, `/categories/`), `/api/cart/` (orders app, cart views), `/api/orders/` (orders app, order views — being wired up in Phase 5).

### DRF global defaults (`settings.py` → `REST_FRAMEWORK`)
JWT authentication + `IsAuthenticated` by default (everything is locked down unless a view opts out), `DjangoFilterBackend`/`SearchFilter`/`OrderingFilter`, page size 12. Because the default is `IsAuthenticated`, any public endpoint (e.g. product browsing) must **explicitly** relax permissions.

### `accounts` — custom email-based auth
Custom user model **`accounts.User`** (`AUTH_USER_MODEL`): `username = None`, `USERNAME_FIELD = 'email'`, with a custom `UserManager` (`managers.py`) — this is why `createsuperuser` asks for an email. A `Profile` (1:1) holds phone/address and is created at registration. Auth uses **SimpleJWT** with refresh-token **rotation + blacklist** (the `token_blacklist` app), so logout genuinely invalidates tokens. `AUTH_USER_MODEL` was set before the first migration — changing it later would require a DB reset.

### `products` — catalog
`Category 1─<N Product`. Both auto-generate a unique slug via `unique_slugify()` (appends `-1`, `-2`… on collision). Served through **ViewSets + DefaultRouter**, keyed by `slug`. Permission `IsAdminOrReadOnly` (`permissions.py`): anyone reads, only `is_staff` writes. `ProductViewSet.get_queryset()` hides `is_available=False` products from non-staff. `ProductFilter` (`filters.py`) adds `min_price`/`max_price`/`in_stock`/`category`. `CategoryViewSet.destroy()` catches `ProtectedError` → clean 409 (category FK is `PROTECT`).

### `orders` — cart + orders (same app)
Cart: `Cart` (1:1 user) and `CartItem` (`unique_together(cart, product)` so re-adding a product increments quantity instead of duplicating). Cart views are plain `APIView`s scoped to `request.user.cart`. Orders (Phase 5): `Order` (FK user `PROTECT`, auto `order_number` like `ORD-20261103-7F3A9C`, `status` via `Order.Status` TextChoices default `pending`) and `OrderItem` (FK product `SET_NULL` + `product_name`/`price` **snapshots** so history survives catalog changes). Checkout (`PlaceOrderView`) runs in a single `transaction.atomic()` with `select_for_update()` row locks: revalidate stock → create order → snapshot lines → deduct stock → clear cart. Admin-only status changes are gated by `ALLOWED_TRANSITIONS` (no auto-`paid`; there is no payment gateway yet).

## Conventions to follow

- **Money is always `DecimalField`, computed on the backend.** Never trust or accept a price from the client. Totals/subtotals derive from stored/ snapshot prices.
- **Per-user resource ownership** is enforced by scoping querysets to `request.user` (e.g. `Order.objects.filter(user=request.user)`), so another user's object id/number resolves to 404 rather than leaking data.
- **`on_delete` choices are deliberate** and encode business rules: `Category`←`Product` = `PROTECT`; `CartItem.product` = `CASCADE`; `Order.user` = `PROTECT`; `OrderItem.product` = `SET_NULL` (+ snapshots). Preserve these intentions.
- **Stock-mutating writes use `transaction.atomic()` + `select_for_update()`** to prevent overselling. Reuse this pattern for any new checkout-like flow.
- Append new apps to `LOCAL_APPS` and include their `urls.py` in `config/urls.py` under `/api/`.

## Development phases

Work proceeds phase-by-phase with explicit owner approval between phases; do not jump ahead. Status: **Phases 1–5 complete** (backend foundation, JWT auth, product catalog, shopping cart, order management — all verified via curl). Orders live in the `orders` app (`Order`/`OrderItem`, routes in `orders/order_urls.py` under `/api/orders/`, migration `0002`). Later phases: AI assistant (Ollama), then the React frontend in `frontend/`.
